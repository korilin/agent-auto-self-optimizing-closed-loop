# Repo Workflow Checklist

## When to trigger this skill

- Modify root scripts under `scripts/`.
- Modify installable skill under `skills/agent-optsmith-loop/`.
- Change metrics logic, weekly review logic, or skill packaging.
- Prepare release, tag, or major refactor of this repository.

## Required steps before commit

1. If root runtime scripts changed, run:
   - `.agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh`
2. Run:
   - `.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh`
3. Keep README English/Chinese synchronized:
   - update both `README.md` and `README_CN.md`
   - keep `README_SYNC_VERSION` marker identical
   - run `.agents/skills/optsmith-repo-maintainer/scripts/check_readme_sync.sh`
4. Update docs when behavior or command usage changed:
   - `README.md`
   - `README_CN.md`
   - `docs/project-integration-guide-cn.md`
5. Auto-commit and auto-push after all checks pass:
   - `.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh --message "<commit-message>"`
   - default behavior includes task logging via `scripts/auto_run_loop.sh` before commit
   - default behavior pushes to remote after commit
   - if strict telemetry is required, add `--enforce-telemetry`
   - skip logging only for exceptions: `--skip-loop`
   - skip push only for exceptions: `--no-push`

## Optional local skill install

To make this project-specific skill available to Codex locally:

- `.agents/skills/optsmith-repo-maintainer/scripts/install_to_codex.sh`

After install, restart Codex.
