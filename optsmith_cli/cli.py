#!/usr/bin/env python3
"""CLI entrypoint for operating the Agent Optsmith skill."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from optsmith_cli import __version__


SKILL_NAME = "agent-optsmith"
DEFAULT_SKILL_DIR = ".agents/skills"
DEFAULT_DATA_DIR = ".agents/optsmith-data"
BLOCK_START = "<!-- OPTSMITH-SKILL:START -->"
BLOCK_END = "<!-- OPTSMITH-SKILL:END -->"


class CliError(RuntimeError):
    """Expected CLI errors with user-facing messages."""


def _run(cmd: list[str], env: Optional[dict[str, str]] = None) -> None:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        subprocess.run(cmd, check=True, env=merged_env)
    except PermissionError as exc:
        raise CliError(
            f"permission denied when executing: {cmd[0]}\n"
            "hint: check file permissions or invoke shell scripts via bash."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise CliError(f"command failed (exit={exc.returncode}): {' '.join(cmd)}") from exc


def _run_shell_script(script_path: Path, script_args: list[str], env: Optional[dict[str, str]] = None) -> None:
    if not script_path.is_file():
        raise CliError(f"missing script: {script_path}")
    _run(["/bin/bash", str(script_path), *script_args], env=env)


def _workspace_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def _is_within_workspace(target: Path, workspace: Path) -> bool:
    try:
        target.relative_to(workspace)
        return True
    except ValueError:
        return False


def _resolve_decl_path(workspace: Path, decl: str, field_name: str) -> Path:
    p = Path(decl).expanduser()
    if not p.is_absolute():
        p = workspace / p
    p = p.resolve()
    if not _is_within_workspace(p, workspace):
        raise CliError(
            f"{field_name} must resolve inside workspace.\n"
            f"workspace: {workspace}\n"
            f"{field_name}: {p}"
        )
    return p


def _agents_file(workspace: Path) -> Path:
    return workspace / "AGENTS.md"


def _extract_agents_block(original: str) -> tuple[int, int, str] | tuple[None, None, None]:
    start_idx = original.find(BLOCK_START)
    end_idx = original.find(BLOCK_END)
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return None, None, None
    end_pos = end_idx + len(BLOCK_END)
    return start_idx, end_pos, original[start_idx:end_pos]


def _extract_block_decl(block_text: str, key: str) -> Optional[str]:
    pattern = re.compile(rf"^-\\s*{re.escape(key)}:\\s*`([^`]+)`\\s*$", re.MULTILINE)
    m = pattern.search(block_text)
    if not m:
        return None
    return m.group(1).strip()


def _read_agents_config(workspace: Path) -> tuple[Optional[str], Optional[str], bool]:
    file_path = _agents_file(workspace)
    if not file_path.exists():
        return None, None, False
    content = file_path.read_text(encoding="utf-8")
    _, _, block_text = _extract_agents_block(content)
    if block_text is None:
        return None, None, False
    skill_dir = _extract_block_decl(block_text, "skill_dir")
    data_dir = _extract_block_decl(block_text, "data_dir")
    return skill_dir, data_dir, True


def _agents_block(skill_dir_decl: str, data_dir_decl: str) -> str:
    return (
        f"{BLOCK_START}\n"
        "## Agent Optsmith Integration\n"
        f"- skill: `{SKILL_NAME}`\n"
        f"- skill_dir: `{skill_dir_decl}`\n"
        f"- data_dir: `{data_dir_decl}`\n"
        "- At task completion, run `optsmith run ...`.\n"
        f"{BLOCK_END}\n"
    )


def _upsert_agents_block(workspace: Path, skill_dir_decl: str, data_dir_decl: str) -> Path:
    agents_file = _agents_file(workspace)
    block = _agents_block(skill_dir_decl=skill_dir_decl, data_dir_decl=data_dir_decl)
    if agents_file.exists():
        original = agents_file.read_text(encoding="utf-8")
    else:
        original = "# AGENTS.md\n\n"

    start_idx, end_pos, _ = _extract_agents_block(original)
    if start_idx is not None and end_pos is not None:
        updated = f"{original[:start_idx].rstrip()}\n\n{block}{original[end_pos:].lstrip()}"
    else:
        tail = "" if original.endswith("\n") else "\n"
        updated = f"{original}{tail}\n{block}"

    agents_file.write_text(updated, encoding="utf-8")
    return agents_file


def _remove_agents_block(workspace: Path) -> Path:
    agents_file = _agents_file(workspace)
    if not agents_file.exists():
        raise CliError(f"missing AGENTS.md: {agents_file}")
    original = agents_file.read_text(encoding="utf-8")
    start_idx, end_pos, _ = _extract_agents_block(original)
    if start_idx is None or end_pos is None:
        raise CliError("OPTSMITH-SKILL managed block not found in AGENTS.md")

    updated = f"{original[:start_idx].rstrip()}\n\n{original[end_pos:].lstrip()}"
    agents_file.write_text(updated, encoding="utf-8")
    return agents_file


def _resolve_runtime_config(
    workspace: Path,
    skill_dir_arg: Optional[str],
    data_dir_arg: Optional[str],
) -> tuple[str, str, Path, Path]:
    block_skill_dir, block_data_dir, _ = _read_agents_config(workspace)
    skill_dir_decl = skill_dir_arg or block_skill_dir or DEFAULT_SKILL_DIR
    data_dir_decl = data_dir_arg or block_data_dir or DEFAULT_DATA_DIR

    skill_root = _resolve_decl_path(workspace, skill_dir_decl, "skill_dir")
    data_root = _resolve_decl_path(workspace, data_dir_decl, "data_dir")
    return skill_dir_decl, data_dir_decl, skill_root, data_root


def _bundled_skill_source() -> Path:
    module_dir = Path(__file__).resolve().parent
    candidates = [
        module_dir / "resources" / "skills" / SKILL_NAME,
        module_dir.parent / "skills" / SKILL_NAME,
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise CliError(
        "bundled skill assets not found for this CLI installation.\n"
        "expected one of:\n"
        + "\n".join(f"- {p}" for p in candidates)
    )


def _install_skill_to_workspace(skill_root: Path) -> Path:
    src = _bundled_skill_source()
    dst = skill_root / SKILL_NAME
    skill_root.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def _ensure_project_skill(skill_root: Path, auto_update: bool) -> Path:
    skill_dir = skill_root / SKILL_NAME
    if skill_dir.is_dir():
        return skill_dir
    if auto_update:
        print(f"info: {SKILL_NAME} not found in workspace, running update...", file=sys.stderr)
        return _install_skill_to_workspace(skill_root)
    raise CliError(
        f"project skill not found: {skill_dir}\n"
        "hint: run `optsmith install` or `optsmith update` first."
    )


def _cmd_install(args: argparse.Namespace) -> int:
    workspace = _workspace_path(args.workspace)
    skill_dir_decl, data_dir_decl, skill_root, data_root = _resolve_runtime_config(
        workspace=workspace,
        skill_dir_arg=args.skill_path,
        data_dir_arg=args.data_dir,
    )

    skill_dir = _install_skill_to_workspace(skill_root)
    setup_script = skill_dir / "scripts" / "setup_loop_workspace.sh"
    env = {
        "OPTSMITH_WORKSPACE_DIR": str(workspace),
        "OPTSMITH_DATA_ROOT": str(data_root),
    }
    _run_shell_script(setup_script, ["--workspace", str(workspace)], env=env)

    if not args.skip_agents:
        agents_file = _upsert_agents_block(
            workspace=workspace,
            skill_dir_decl=skill_dir_decl,
            data_dir_decl=data_dir_decl,
        )
        print(f"updated: {agents_file}")

    print(f"installed project skill: {skill_dir}")
    print(f"data dir: {data_root}")
    print(f"workspace: {workspace}")
    return 0


def _cmd_update(args: argparse.Namespace) -> int:
    workspace = _workspace_path(args.workspace)
    skill_dir_decl, data_dir_decl, skill_root, _ = _resolve_runtime_config(
        workspace=workspace,
        skill_dir_arg=args.skill_path,
        data_dir_arg=args.data_dir,
    )

    skill_dir = _install_skill_to_workspace(skill_root)

    if not args.skip_agents:
        agents_file = _upsert_agents_block(
            workspace=workspace,
            skill_dir_decl=skill_dir_decl,
            data_dir_decl=data_dir_decl,
        )
        print(f"updated: {agents_file}")

    print(f"updated project skill: {skill_dir}")
    return 0


def _cmd_uninstall(args: argparse.Namespace) -> int:
    workspace = _workspace_path(args.workspace)
    block_skill_dir, block_data_dir, has_block = _read_agents_config(workspace)
    if not has_block:
        raise CliError("OPTSMITH-SKILL managed block not found in AGENTS.md")

    skill_dir_decl = block_skill_dir or DEFAULT_SKILL_DIR
    data_dir_decl = block_data_dir or DEFAULT_DATA_DIR
    skill_root = _resolve_decl_path(workspace, skill_dir_decl, "skill_dir")
    data_root = _resolve_decl_path(workspace, data_dir_decl, "data_dir")
    skill_dir = skill_root / SKILL_NAME

    removed: list[str] = []
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
        removed.append(str(skill_dir))
    if data_root.exists():
        shutil.rmtree(data_root)
        removed.append(str(data_root))

    agents_file = _remove_agents_block(workspace)
    print(f"updated: {agents_file}")
    if removed:
        for item in removed:
            print(f"removed: {item}")
    else:
        print("nothing to remove: skill/data directories already absent")
    return 0


def _cmd_dashboard(args: argparse.Namespace) -> int:
    workspace = _workspace_path(args.workspace)
    _, _, skill_root, data_root = _resolve_runtime_config(
        workspace=workspace,
        skill_dir_arg=args.skill_path,
        data_dir_arg=args.data_dir,
    )
    skill_dir = _ensure_project_skill(skill_root=skill_root, auto_update=not args.no_auto_update)

    dashboard_script = skill_dir / "scripts" / "dashboard_server.sh"
    env = {
        "OPTSMITH_WORKSPACE_DIR": str(workspace),
        "OPTSMITH_DATA_ROOT": str(data_root),
    }
    _run_shell_script(dashboard_script, ["--host", args.host, "--port", str(args.port)], env=env)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    workspace = _workspace_path(args.workspace)
    _, _, skill_root, data_root = _resolve_runtime_config(
        workspace=workspace,
        skill_dir_arg=args.skill_path,
        data_dir_arg=args.data_dir,
    )
    skill_dir = _ensure_project_skill(skill_root=skill_root, auto_update=not args.no_auto_update)
    auto_run_script = skill_dir / "scripts" / "auto_run_loop.sh"
    env = {
        "OPTSMITH_WORKSPACE_DIR": str(workspace),
        "OPTSMITH_DATA_ROOT": str(data_root),
    }
    _run_shell_script(auto_run_script, args.forward_args, env=env)
    return 0


def _cmd_metrics(args: argparse.Namespace) -> int:
    workspace = _workspace_path(args.workspace)
    _, _, skill_root, data_root = _resolve_runtime_config(
        workspace=workspace,
        skill_dir_arg=args.skill_path,
        data_dir_arg=args.data_dir,
    )
    skill_dir = _ensure_project_skill(skill_root=skill_root, auto_update=not args.no_auto_update)
    metrics_script = skill_dir / "scripts" / "metrics_report.sh"
    env = {
        "OPTSMITH_WORKSPACE_DIR": str(workspace),
        "OPTSMITH_DATA_ROOT": str(data_root),
    }
    forward_args = list(args.forward_args)
    if not forward_args:
        forward_args = ["--all"]
    _run_shell_script(metrics_script, forward_args, env=env)
    return 0


def _cmd_optimize(args: argparse.Namespace) -> int:
    workspace = _workspace_path(args.workspace)
    _, _, skill_root, data_root = _resolve_runtime_config(
        workspace=workspace,
        skill_dir_arg=args.skill_path,
        data_dir_arg=args.data_dir,
    )
    skill_dir = _ensure_project_skill(skill_root=skill_root, auto_update=not args.no_auto_update)
    optimize_script = skill_dir / "scripts" / "optimize_skill.sh"
    env = {
        "OPTSMITH_WORKSPACE_DIR": str(workspace),
        "OPTSMITH_DATA_ROOT": str(data_root),
    }
    _run_shell_script(optimize_script, args.forward_args, env=env)
    return 0


def _cmd_version(args: argparse.Namespace) -> int:
    del args
    print(__version__)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="optsmith",
        description="Agent Optsmith CLI for project-local installation, updates, telemetry, and optimization.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="show CLI version",
    )
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="initialize workspace and install project-local skill")
    install_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    install_parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help=f"data directory (default: {DEFAULT_DATA_DIR})")
    install_parser.add_argument("--skill-path", default=DEFAULT_SKILL_DIR, help=f"skill root directory (default: {DEFAULT_SKILL_DIR})")
    install_parser.add_argument("--skip-agents", action="store_true", help="do not update AGENTS.md managed block")
    install_parser.set_defaults(func=_cmd_install)

    update_parser = subparsers.add_parser("update", help="update project-installed skill to current CLI version")
    update_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    update_parser.add_argument("--skill-path", default=None, help="skill root directory (default: AGENTS block or .agents/skills)")
    update_parser.add_argument("--data-dir", default=None, help="data directory (default: AGENTS block or .agents/optsmith-data)")
    update_parser.add_argument("--skip-agents", action="store_true", help="do not update AGENTS.md managed block")
    update_parser.set_defaults(func=_cmd_update)

    uninstall_parser = subparsers.add_parser("uninstall", help="remove managed AGENTS block, data dir, and installed project skill")
    uninstall_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    uninstall_parser.set_defaults(func=_cmd_uninstall)

    dashboard_parser = subparsers.add_parser("dashboard", help="start local dashboard for selected project")
    dashboard_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="dashboard host (default: 127.0.0.1)")
    dashboard_parser.add_argument("--port", type=int, default=8765, help="dashboard port (default: 8765)")
    dashboard_parser.add_argument("--skill-path", default=None, help="skill root directory override")
    dashboard_parser.add_argument("--data-dir", default=None, help="data directory override")
    dashboard_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `optsmith update`")
    dashboard_parser.set_defaults(func=_cmd_dashboard)

    run_parser = subparsers.add_parser("run", help="run project automation command")
    run_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    run_parser.add_argument("--skill-path", default=None, help="skill root directory override")
    run_parser.add_argument("--data-dir", default=None, help="data directory override")
    run_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `optsmith update`")
    run_parser.set_defaults(func=_cmd_run)

    metrics_parser = subparsers.add_parser("metrics", help="run metrics report command")
    metrics_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    metrics_parser.add_argument("--skill-path", default=None, help="skill root directory override")
    metrics_parser.add_argument("--data-dir", default=None, help="data directory override")
    metrics_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `optsmith update`")
    metrics_parser.set_defaults(func=_cmd_metrics)

    optimize_parser = subparsers.add_parser("optimize", help="run optimize skill command")
    optimize_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    optimize_parser.add_argument("--skill-path", default=None, help="skill root directory override")
    optimize_parser.add_argument("--data-dir", default=None, help="data directory override")
    optimize_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `optsmith update`")
    optimize_parser.set_defaults(func=_cmd_optimize)

    version_parser = subparsers.add_parser("version", help="show CLI version")
    version_parser.set_defaults(func=_cmd_version)

    help_parser = subparsers.add_parser("help", help="show help")
    help_parser.add_argument(
        "topic",
        nargs="?",
        choices=["install", "update", "uninstall", "dashboard", "run", "metrics", "optimize", "version", "help"],
    )
    help_parser.set_defaults(func=None)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args, unknown = parser.parse_known_args(argv)

    forward_commands = {"run", "metrics", "optimize"}
    if args.command in forward_commands:
        args.forward_args = unknown
    elif unknown:
        parser.error(f"unknown arguments: {' '.join(unknown)}")

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "help":
        topic = args.topic
        if topic is None:
            parser.print_help()
        else:
            subparser = _build_parser()
            sub_args = [topic, "--help"]
            subparser.parse_args(sub_args)
        return 0

    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 1

    try:
        return int(func(args))
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
