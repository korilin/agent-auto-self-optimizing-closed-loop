#!/usr/bin/env python3
"""CLI entrypoint for operating the agent-self-optimizing-loop skill."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


DEFAULT_REPO = "korilin/agent-auto-self-optimizing-closed-loop"
DEFAULT_SKILL_PATH = "skills/agent-self-optimizing-loop"
BLOCK_START = "<!-- AOSO-SKILL:START -->"
BLOCK_END = "<!-- AOSO-SKILL:END -->"


class CliError(RuntimeError):
    """Expected CLI errors with user-facing messages."""


def _codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    return Path(raw).expanduser().resolve()


def _skill_home() -> Path:
    return _codex_home() / "skills" / "agent-self-optimizing-loop"


def _installer_script() -> Path:
    return _codex_home() / "skills" / ".system" / "skill-installer" / "scripts" / "install-skill-from-github.py"


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


def _install_skill(repo: str, skill_path: str) -> None:
    installer = _installer_script()
    if not installer.is_file():
        raise CliError(
            f"skill-installer not found: {installer}\n"
            "hint: ensure Codex system skill `skill-installer` is available."
        )
    cmd = [sys.executable, str(installer), "--repo", repo, "--path", skill_path]
    _run(cmd)


def _ensure_skill_installed(repo: str, skill_path: str, auto_install: bool) -> Path:
    skill_home = _skill_home()
    if skill_home.is_dir():
        return skill_home
    if auto_install:
        print("info: agent-self-optimizing-loop not found locally, running update...", file=sys.stderr)
        _install_skill(repo=repo, skill_path=skill_path)
        if skill_home.is_dir():
            return skill_home
    raise CliError(
        f"skill not found: {skill_home}\n"
        "hint: run `aoso-skill update` first."
    )


def _agents_block() -> str:
    return (
        f"{BLOCK_START}\n"
        "## AOSO Skill Integration\n"
        "- Always load and use `agent-self-optimizing-loop` for project tasks.\n"
        "- At task completion, run `aoso-skill run ...`.\n"
        "- Use `aoso-skill dashboard` to open the local dashboard.\n"
        f"{BLOCK_END}\n"
    )


def _upsert_agents_block(workspace: Path) -> Path:
    agents_file = workspace / "AGENTS.md"
    block = _agents_block()
    if agents_file.exists():
        original = agents_file.read_text(encoding="utf-8")
    else:
        original = "# AGENTS.md\n\n"

    start_idx = original.find(BLOCK_START)
    end_idx = original.find(BLOCK_END)
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        end_pos = end_idx + len(BLOCK_END)
        updated = f"{original[:start_idx].rstrip()}\n\n{block}{original[end_pos:].lstrip()}"
    else:
        tail = "" if original.endswith("\n") else "\n"
        updated = f"{original}{tail}\n{block}"

    agents_file.write_text(updated, encoding="utf-8")
    return agents_file


def _cmd_update(args: argparse.Namespace) -> int:
    _install_skill(repo=args.repo, skill_path=args.skill_path)
    print(f"updated: {_skill_home()}")
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    skill_home = _ensure_skill_installed(
        repo=args.repo,
        skill_path=args.skill_path,
        auto_install=not args.no_auto_update,
    )

    setup_script = skill_home / "scripts" / "setup_loop_workspace.sh"
    _run_shell_script(setup_script, ["--workspace", str(workspace)])

    if not args.skip_agents:
        agents_file = _upsert_agents_block(workspace)
        print(f"updated: {agents_file}")

    print(f"initialized workspace: {workspace}")
    print("next: use `aoso-skill dashboard` to open the web dashboard")
    return 0


def _cmd_dashboard(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    skill_home = _ensure_skill_installed(
        repo=args.repo,
        skill_path=args.skill_path,
        auto_install=not args.no_auto_update,
    )

    dashboard_script = skill_home / "scripts" / "dashboard_server.sh"
    env = {"AOSO_WORKSPACE_DIR": str(workspace)}
    _run_shell_script(dashboard_script, ["--host", args.host, "--port", str(args.port)], env=env)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    skill_home = _ensure_skill_installed(
        repo=args.repo,
        skill_path=args.skill_path,
        auto_install=not args.no_auto_update,
    )
    auto_run_script = skill_home / "scripts" / "auto_run_loop.sh"
    env = {"AOSO_WORKSPACE_DIR": str(workspace)}
    _run_shell_script(auto_run_script, args.forward_args, env=env)
    return 0


def _cmd_metrics(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    skill_home = _ensure_skill_installed(
        repo=args.repo,
        skill_path=args.skill_path,
        auto_install=not args.no_auto_update,
    )
    metrics_script = skill_home / "scripts" / "metrics_report.sh"
    env = {"AOSO_WORKSPACE_DIR": str(workspace)}
    forward_args = list(args.forward_args)
    if not forward_args:
        forward_args = ["--all"]
    _run_shell_script(metrics_script, forward_args, env=env)
    return 0


def _cmd_optimize(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    skill_home = _ensure_skill_installed(
        repo=args.repo,
        skill_path=args.skill_path,
        auto_install=not args.no_auto_update,
    )
    optimize_script = skill_home / "scripts" / "optimize_skill.sh"
    env = {"AOSO_WORKSPACE_DIR": str(workspace)}
    _run_shell_script(optimize_script, args.forward_args, env=env)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aoso-skill",
        description="Operate the agent-self-optimizing-loop skill without git submodule setup.",
    )
    subparsers = parser.add_subparsers(dest="command")

    update_parser = subparsers.add_parser("update", help="install or update agent-self-optimizing-loop skill")
    update_parser.add_argument("--repo", default=DEFAULT_REPO, help=f"github repo (default: {DEFAULT_REPO})")
    update_parser.add_argument("--skill-path", default=DEFAULT_SKILL_PATH, help=f"repo path (default: {DEFAULT_SKILL_PATH})")
    update_parser.set_defaults(func=_cmd_update)

    init_parser = subparsers.add_parser("init", help="initialize current project for self-optimizing loop")
    init_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    init_parser.add_argument("--skip-agents", action="store_true", help="do not update AGENTS.md managed block")
    init_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `aoso-skill update`")
    init_parser.add_argument("--repo", default=DEFAULT_REPO, help=argparse.SUPPRESS)
    init_parser.add_argument("--skill-path", default=DEFAULT_SKILL_PATH, help=argparse.SUPPRESS)
    init_parser.set_defaults(func=_cmd_init)

    dashboard_parser = subparsers.add_parser("dashboard", help="start local dashboard for selected project")
    dashboard_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="dashboard host (default: 127.0.0.1)")
    dashboard_parser.add_argument("--port", type=int, default=8765, help="dashboard port (default: 8765)")
    dashboard_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `aoso-skill update`")
    dashboard_parser.add_argument("--repo", default=DEFAULT_REPO, help=argparse.SUPPRESS)
    dashboard_parser.add_argument("--skill-path", default=DEFAULT_SKILL_PATH, help=argparse.SUPPRESS)
    dashboard_parser.set_defaults(func=_cmd_dashboard)

    run_parser = subparsers.add_parser("run", help="run auto loop collection+analysis command")
    run_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    run_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `aoso-skill update`")
    run_parser.add_argument("--repo", default=DEFAULT_REPO, help=argparse.SUPPRESS)
    run_parser.add_argument("--skill-path", default=DEFAULT_SKILL_PATH, help=argparse.SUPPRESS)
    run_parser.set_defaults(func=_cmd_run)

    metrics_parser = subparsers.add_parser("metrics", help="run metrics report command")
    metrics_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    metrics_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `aoso-skill update`")
    metrics_parser.add_argument("--repo", default=DEFAULT_REPO, help=argparse.SUPPRESS)
    metrics_parser.add_argument("--skill-path", default=DEFAULT_SKILL_PATH, help=argparse.SUPPRESS)
    metrics_parser.set_defaults(func=_cmd_metrics)

    optimize_parser = subparsers.add_parser("optimize", help="run optimize skill command")
    optimize_parser.add_argument("--workspace", default=".", help="project workspace (default: current directory)")
    optimize_parser.add_argument("--no-auto-update", action="store_true", help="fail instead of auto-running `aoso-skill update`")
    optimize_parser.add_argument("--repo", default=DEFAULT_REPO, help=argparse.SUPPRESS)
    optimize_parser.add_argument("--skill-path", default=DEFAULT_SKILL_PATH, help=argparse.SUPPRESS)
    optimize_parser.set_defaults(func=_cmd_optimize)

    help_parser = subparsers.add_parser("help", help="show help")
    help_parser.add_argument("topic", nargs="?", choices=["init", "update", "dashboard", "run", "metrics", "optimize", "help"])
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
