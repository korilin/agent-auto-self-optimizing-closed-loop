---
name: aoso-repo-maintainer
description: Maintain and evolve the agent-auto-self-optimizing-closed-loop repository with a strict local workflow. Use when tasks modify this repository's scripts, docs, CI, or bundled skills, especially when runtime scripts and the installable skill must stay in sync and repository-level validation is required before commit.
---

# AOSO Repo Maintainer

This skill is project-local and intended only for `agent-auto-self-optimizing-closed-loop`.

## Scope

- Keep runtime scripts under `scripts/` and installable skill scripts under `skills/agent-self-optimizing-loop/scripts/` synchronized.
- Run repository validation workflow before commit.
- Keep docs consistent with changed commands and behavior.
- Optionally install this project-local skill into local Codex skill home.

## Workflow

1. If root runtime scripts changed, run:
```bash
skills/aoso-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh
```

2. Run repository validation:
```bash
skills/aoso-repo-maintainer/scripts/validate_repo_workflow.sh
```

3. If command behavior changed, update:
- `README.md`
- `README_CN.md`
- `docs/project-integration-guide-cn.md`

4. If this skill changed and should be active locally, install it:
```bash
skills/aoso-repo-maintainer/scripts/install_to_codex.sh
```

5. Commit only after workflow checks pass.

## References

- For trigger and commit checklist, read:
  - `references/repo-workflow-checklist.md`

## Scripts

- `scripts/sync_runtime_to_installable_skill.sh`: Copy runtime scripts into installable skill.
- `scripts/validate_repo_workflow.sh`: Syntax/parity/smoke checks for this repository.
- `scripts/install_to_codex.sh`: Install this project-local skill into `$CODEX_HOME/skills`.
