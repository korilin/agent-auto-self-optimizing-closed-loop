# AGENTS.md

## Mission

Deliver high-quality outcomes while reducing average token cost per task over time.

## Core KPIs

- `success_rate`: Completed tasks without rework.
- `avg_tokens_per_task`: Mean token usage per completed task.
- `rework_rate`: Fraction of tasks reopened after first delivery.
- `skill_hit_rate`: Fraction of tasks solved with existing skills.

## Operating Loop

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

## Project-Local Skill

Use project-local skill `aoso-repo-maintainer` for repository maintenance tasks:

- path: `skills/aoso-repo-maintainer/`
- trigger: any change to `scripts/`, `skills/`, CI, or workflow docs.
- required workflow:
  1. `skills/aoso-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh` (when runtime scripts changed)
  2. Update docs when command behavior changed.
  3. `skills/aoso-repo-maintainer/scripts/check_readme_sync.sh` (README.md and README_CN.md must stay synchronized)
  4. `skills/aoso-repo-maintainer/scripts/validate_repo_workflow.sh`
  5. `skills/aoso-repo-maintainer/scripts/auto_commit.sh --message "<commit-message>"`

## Automation Policy

- Prefer `scripts/auto_run_loop.sh` / `skills/agent-self-optimizing-loop/scripts/auto_run_loop.sh` over manual multi-command operation.
- Prefer dashboard filtering via `scripts/dashboard_server.sh` for interactive metric analysis.

## Error KB Policy

For every notable failure, create one file under `knowledge-base/errors/` named:

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
