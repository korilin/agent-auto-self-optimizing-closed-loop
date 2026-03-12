# AGENTS.md

## Mission

Deliver high-quality outcomes while reducing average token cost per task over time.

## Core KPIs

- `success_rate`: Completed tasks without rework.
- `avg_tokens_per_task`: Mean token usage per completed task.
- `rework_rate`: Fraction of tasks reopened after first delivery.
- `skill_hit_rate`: Fraction of tasks solved with existing skills.

## Operating Workflow

1. Classify request by task type and risk.
2. Reuse existing skill if available; avoid rebuilding context from scratch.
3. Execute with the minimum context needed and run automation scripts for repeatable data capture.
4. Validate output with concrete checks (tests, lint, expected files).
5. Record failures and high-cost runs in knowledge base.
6. Promote proven fixes into `AGENTS.md` or skills.

## Token Policy

- Keep high-level policy in this file; move details to references.
- Prefer scripts for repeated deterministic work.
- Avoid duplicating the same guidance across files.
- Store large schemas and examples under `references/`, not in main prompts.
- Summarize long execution outputs before carrying them forward.

## Skill Lifecycle Policy

Create or update a skill when any condition is true:

- Same workflow appears `>= 3` times in 7 days.
- Average token cost is significantly above baseline for that task type.
- Failure recurs with the same root cause twice.

Skill quality gates:

1. Name is normalized to lowercase hyphen-case.
2. `SKILL.md` keeps only core workflow and trigger guidance.
3. Variant details live in `references/`.
4. Repeated code lives in `scripts/` and is executable.
5. Skill is validated before adoption.

## Project-Local Skills

Use `optsmith-repo-maintainer` for repository maintenance tasks:

- path: `.agents/skills/optsmith-repo-maintainer/`
- trigger: changes to `scripts/`, `.agents/skills/`, `skills/`, CI, or workflow docs.
- required workflow:
  1. `.agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh` (when runtime scripts changed)
  2. Update docs when command behavior changed.
  3. `.agents/skills/optsmith-repo-maintainer/scripts/check_readme_sync.sh` (README.md and README_CN.md must stay synchronized)
  4. `.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh`
  5. `.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh --message "<commit-message>"`

Use `optsmith-cli-maintainer` for CLI behavior and release/versioning tasks:

- path: `.agents/skills/optsmith-cli-maintainer/`
- trigger: changes under `optsmith_cli/`, `pyproject.toml`, or `Formula/optsmith.rb`.
- required workflow:
  1. Keep CLI command contract backward-compatible when possible.
  2. If CLI changed, bump version in all three files together:
     - `pyproject.toml`
     - `optsmith_cli/__init__.py`
     - `Formula/optsmith.rb`
  3. `.agents/skills/optsmith-cli-maintainer/scripts/check_cli_version_bump.sh`
  4. `.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh`
  5. `.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh --message "<commit-message>"`

Use `optsmith-workflow-maintainer` for GitHub workflow reliability tasks:

- path: `.agents/skills/optsmith-workflow-maintainer/`
- trigger: changes to `.github/workflows/*` or workflow validation logic.
- required workflow:
  1. Keep CI smoke checks side-effect safe (use temp data paths).
  2. Keep workflow run blocks debuggable (`set -euxo pipefail`).
  3. `.agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh`
  4. `.agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh`
  5. `.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh --message "<commit-message>"`

## Automation Policy

- Prefer `scripts/auto_run_loop.sh` / `skills/agent-optsmith/scripts/auto_run_loop.sh` over manual multi-command operation.
- Prefer dashboard filtering via `scripts/dashboard_server.sh` for interactive metric analysis.
- Use `scripts/optimize_skill.sh` (or dashboard trigger) to generate explicit optimization plans per skill.

## Error KB Policy

For every notable failure, create one file under `.agents/optsmith-data/knowledge-base/errors/` named:

`YYYY-MM-DD-short-slug.md`

Required fields:

- date
- task_type
- severity
- symptom
- root_cause
- fix
- prevention_rule
- trigger_signals
- token_cost_estimate
- status

## Weekly Governance

Run `./scripts/weekly_review.sh` once per week and review:

1. Top recurring root causes.
2. High-cost task types.
3. Skills to add, split, or simplify.
4. Rules to promote, rewrite, or remove.

## Change Control

- Add rules only if backed by at least one concrete incident or measurable gain.
- Remove rules that no longer provide measurable value.
- Keep policy concise and operational.

## Definition of Done

- Task result is correct and verifiable.
- Token usage is logged when unusually high.
- New failures are captured in error KB.
- Follow-up rule/skill updates are clearly identified.

<!-- OPTSMITH-SKILL:START -->
## Agent Optsmith Integration
- skill: `agent-optsmith`
- skill_dir: `.agents/skills`
- data_dir: `.agents/optsmith-data`
- At task completion, run `optsmith run ...`.
<!-- OPTSMITH-SKILL:END -->
