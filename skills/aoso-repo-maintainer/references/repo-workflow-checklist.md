# Repo Workflow Checklist

## When to trigger this skill

- Modify root scripts under `scripts/`.
- Modify installable skill under `skills/agent-self-optimizing-loop/`.
- Change metrics logic, weekly review logic, or skill packaging.
- Prepare release, tag, or major refactor of this repository.

## Required steps before commit

1. If root runtime scripts changed, run:
   - `skills/aoso-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh`
2. Run:
   - `skills/aoso-repo-maintainer/scripts/validate_repo_workflow.sh`
3. Update docs when behavior or command usage changed:
   - `README.md`
   - `README_CN.md`
   - `docs/project-integration-guide-cn.md`

## Optional local skill install

To make this project-specific skill available to Codex locally:

- `skills/aoso-repo-maintainer/scripts/install_to_codex.sh`

After install, restart Codex.
