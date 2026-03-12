---
name: optsmith-repo-maintainer
description: Maintain and evolve the agent-optsmith repository with a strict local workflow. Use when tasks modify this repository's scripts, docs, CI, or bundled skills, especially when runtime scripts and the installable skill must stay in sync and repository-level validation is required before commit.
---

# Optsmith Repo Maintainer

This skill is project-local and intended only for `agent-optsmith`.

## Scope

- Keep runtime scripts under `scripts/` and installable skill scripts under `skills/agent-optsmith/scripts/` synchronized.
- Run repository validation workflow before commit.
- Keep English and Chinese README synchronized.
- Keep docs consistent with changed commands and behavior.
- Delegate CLI command-contract, packaging, and version-bump policy to `optsmith-cli-maintainer`.
- Delegate GitHub workflow reliability policy to `optsmith-workflow-maintainer`.
- Optionally install this project-local skill into local Codex skill home.

## Workflow

1. If root runtime scripts changed, run:
```bash
.agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh
```

2. Run repository validation:
```bash
.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh
```

If CLI scope changed (`optsmith_cli/`, `pyproject.toml`, `Formula/optsmith.rb`), also run:
```bash
.agents/skills/optsmith-cli-maintainer/scripts/check_cli_version_bump.sh
```

If workflow scope changed (`.github/workflows/*`), also run:
```bash
.agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh
```

3. Keep `README.md` and `README_CN.md` synchronized:
- Update both files in the same change.
- Keep `README_SYNC_VERSION` marker identical in both files.
- Validate using:
```bash
.agents/skills/optsmith-repo-maintainer/scripts/check_readme_sync.sh
```

4. If command behavior changed, update:
- `README.md`
- `README_CN.md`
- `docs/project-integration-guide-cn.md`

5. Auto-commit after checks pass:
```bash
.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh --message "docs: update workflow"
```

`auto_commit.sh` now runs `scripts/auto_run_loop.sh` automatically before commit
to persist one task-run record and refresh metrics, then pushes by default.
Use `--skip-loop` or `--no-push` only for exceptional cases.

6. If this skill changed and should be active locally, install it:
```bash
.agents/skills/optsmith-repo-maintainer/scripts/install_to_codex.sh
```

7. Commit and push are done by `auto_commit.sh` only after workflow checks pass.

## References

- For trigger and commit checklist, read:
  - `references/repo-workflow-checklist.md`

## Scripts

- `scripts/sync_runtime_to_installable_skill.sh`: Copy runtime scripts into installable skill.
- `scripts/check_readme_sync.sh`: Enforce README English/Chinese synchronization.
- `scripts/validate_repo_workflow.sh`: Syntax/parity/smoke checks for this repository.
- `scripts/auto_commit.sh`: Auto-run loop logging, stage all changes, create one non-interactive commit, and push.
- `scripts/install_to_codex.sh`: Install this project-local skill into `$CODEX_HOME/skills`.

## Auto Optimization Snapshot
<!-- OPTSMITH_AUTO_OPT_START -->
- updated_at: 2026-03-09T17:42:49
- mode: existing
- task_type: n/a
- optimization_status: watch
- opportunity_score: 50
- source_report: /Users/korilin/Documents/github/agent-optsmith/.agents/optsmith-data/reports/skill-optimization/2026-03-09-optsmith-repo-maintainer-optimization-plan.md
- top_actions:
  - Collect at least 10 no-skill baseline samples on the same task types.
- top_root_causes:
  - none
- optimization_log: `references/auto-optimization.md`
<!-- OPTSMITH_AUTO_OPT_END -->
