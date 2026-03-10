# Skill Optimization Plan

## Scope

- skill: aoso-repo-maintainer
- mode: root
- data_file: /Users/korilin/Documents/github/agent-auto-self-optimizing-closed-loop/metrics/task-runs.csv
- kb_dir: /Users/korilin/Documents/github/agent-auto-self-optimizing-closed-loop/knowledge-base/errors
- date_range_start: 2026-03-06
- date_range_end: 2026-03-06
- cutover: 2026-03-06

## Opportunity Assessment

- optimization_status: watch
- opportunity_score: 50
- overlap_task_types: 0
- sample_size_skill: n/a
- sample_size_baseline: n/a
- token_reduction_pct: n/a
- duration_reduction_pct: n/a
- success_rate_delta_pp: n/a
- rework_rate_delta: n/a

## Key Findings

- Insufficient baseline on matching task types.

## Suggested Optimization Actions

1. Collect at least 10 no-skill baseline samples for the same task types.

## Related Root Causes (From Error KB)

- none

## Trigger Command

```bash
/Users/korilin/Documents/github/agent-auto-self-optimizing-closed-loop/scripts/optimize_skill.sh --skill "aoso-repo-maintainer" --start "2026-03-06" --end "2026-03-06" --cutover 2026-03-06
```

## Raw Skill Metrics Output

```text
Overall Metrics
  tasks: 1
  active_days: 1
  tasks_per_day: 1.00
  avg_tokens: 0.00
  avg_duration_sec: 0.00
  success_rate: 100.00%
  rework_rate: 0.00

Pre/Post Metrics (cutover=2026-03-06)
  pre_tasks: 0
  pre_tasks_per_day: n/a
  pre_avg_tokens: n/a
  pre_avg_duration_sec: n/a
  pre_success_rate: n/a
  pre_rework_rate: n/a
  post_tasks: 1
  post_tasks_per_day: 1.00
  post_avg_tokens: 0.00
  post_avg_duration_sec: 0.00
  post_success_rate: 100.00%
  post_rework_rate: 0.00

Skill: aoso-repo-maintainer
  overlap_task_types: 0
  status: insufficient baseline (need no-skill samples on same task_type)
```
