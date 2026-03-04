---
name: agent-self-optimizing-loop
description: Set up and run a project-level self-optimizing loop for AI coding workflows with measurable impact. Use when users ask to introduce self-optimization in a repository, log per-task token and duration metrics, generate weekly error reviews, evaluate how much a skill reduced token usage, or compare engineering productivity before and after optimization changes.
---

# Agent Self-Optimizing Loop

Use this skill to operationalize and measure continuous optimization in any project.

## Required Paths

- Resolve the skill home as: `${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop`
- Use project-local data under `.agent-loop-data/`

## Primary Workflow

1. Initialize project data once:
```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/setup_loop_workspace.sh" --workspace "$(pwd)"
```

2. Log each completed task:
```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/log_task_run.sh" \
  --task-id TASK-1001 \
  --task-type debug \
  --project my-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --total-tokens 1820 \
  --duration-sec 420 \
  --success true
```

3. Record failures in `.agent-loop-data/knowledge-base/errors/` using the generated template:
- `.agent-loop-data/templates/error-entry.md`

4. Generate weekly review:
```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/weekly_review.sh"
```

5. Measure optimization effect:
```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/metrics_report.sh" --all
"${SKILL_HOME}/scripts/metrics_report.sh" --skill log-analysis-helper
"${SKILL_HOME}/scripts/metrics_report.sh" --all --cutover 2026-03-01
```

## Interpretation Rules

- Use `token_reduction_pct` to quantify single-skill token savings.
- Use `duration_reduction_pct` to quantify single-skill cycle-time savings.
- Use `delta_avg_tokens_pct`, `delta_avg_duration_pct`, `delta_tasks_per_day_pct` for engineering pre/post impact.
- Require adequate overlap baseline by task type; do not claim gains without no-skill samples on the same task type.

## Decision Policy

- Create or refactor a skill when the same workflow repeats at least three times in seven days.
- Add or update governance rules only when an incident or metric supports the change.
- Keep prompts lean; move repeated deterministic operations to scripts.

## References

- For command snippets, read `references/command-recipes.md`.

## Scripts

- `scripts/setup_loop_workspace.sh`: Initialize project-local data directories.
- `scripts/log_task_run.sh`: Append one standardized task-run record.
- `scripts/weekly_review.sh`: Build weekly optimization report from error KB.
- `scripts/metrics_report.sh`: Compute overall, per-skill, and pre/post metrics.
