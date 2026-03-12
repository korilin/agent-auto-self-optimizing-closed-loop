---
name: optsmith-workflow-maintainer
description: Maintain GitHub workflow reliability for agent-optsmith. Use when changing `.github/workflows/*`, CI smoke commands, action versions, or workflow-related validation scripts.
---

# Optsmith Workflow Maintainer

This skill is project-local and focused on GitHub workflow quality and stability.

## Scope

- Workflow files under `.github/workflows/`.
- CI smoke command design and reproducibility.
- Workflow-specific validation scripts and guardrails.

## Required Workflow

1. Keep workflow smoke checks deterministic and side-effect safe:
   - prefer temporary data roots instead of writing repository telemetry files.
   - enable command tracing (`set -euxo pipefail`) in CI run blocks.
2. Validate workflow structure and smoke assumptions:
```bash
.agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh
```
3. Run repo-level validation:
```bash
.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh
```
4. Commit and push after checks pass:
```bash
.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh --message "<commit-message>"
```

## References

- `references/workflow-maintenance-checklist.md`

## Scripts

- `scripts/check_ci_workflow.sh`: validate CI workflow structure and run a local workflow smoke subset with temp data paths.
