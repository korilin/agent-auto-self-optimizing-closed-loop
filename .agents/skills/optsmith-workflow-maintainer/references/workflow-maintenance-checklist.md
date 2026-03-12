# Workflow Maintenance Checklist

## When to trigger this skill

- Modify `.github/workflows/ci.yml` or other workflow files.
- Change CI smoke command order, arguments, or environment variables.
- Add/remove workflow-level validation scripts.

## Workflow Rules

1. CI smoke checks must be reproducible:
   - use temp directories for telemetry output during CI.
   - avoid mutating repository-tracked data files in smoke jobs.
2. CI run block should expose failure command clearly:
   - include `set -euxo pipefail`.
3. Workflow maintenance changes must have local verification:
   - run `.agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh`.
4. Keep repository validation in CI:
   - `.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh`

## Required Checks

```bash
bash -n .github/workflows/ci.yml
.agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh
.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh
```
