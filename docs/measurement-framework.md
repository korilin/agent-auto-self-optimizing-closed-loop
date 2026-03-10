# Measurement Framework

## Data Model

Use `.agent-loop-data/metrics/task-runs.csv` with one row per completed task:

- `date`: `YYYY-MM-DD`
- `task_id`: unique identifier
- `task_type`: e.g., `coding`, `debug`, `review`, `docs`, `ops`
- `project`: repo or stream name
- `model`: model name used
- `used_skill`: `true` or `false`
- `skill_name`: skill id when `used_skill=true`, otherwise empty
- `total_tokens`: prompt + completion
- `duration_sec`: end-to-end execution seconds
- `success`: `true` or `false` on first pass
- `rework_count`: how many reopen/retry rounds

## Core Metrics

1. Token efficiency
- `avg_tokens = sum(total_tokens) / tasks`

2. Cycle-time efficiency
- `avg_duration_sec = sum(duration_sec) / tasks`

3. Quality
- `success_rate = success_tasks / tasks`
- `rework_rate = sum(rework_count) / tasks`

4. Throughput
- `tasks_per_day = tasks / active_days`

## Skill Impact (Token Reduction)

For one skill:

1. Collect `used_skill=true AND skill_name=<target>`.
2. For each `task_type`, collect baseline rows with `used_skill=false`.
3. Compare weighted averages on overlapping task types.

Formula:

- `token_reduction_pct = (baseline_avg_tokens - skill_avg_tokens) / baseline_avg_tokens * 100`

Also calculate:

- `duration_reduction_pct`
- `success_rate_delta_pp`
- `rework_delta`

## Engineering Productivity Impact

Use pre/post window with a cutover date:

- `pre`: `date < cutover`
- `post`: `date >= cutover`

Compare:

- `avg_tokens`
- `avg_duration_sec`
- `success_rate`
- `rework_rate`
- `tasks_per_day`

## Guardrails for Fair Comparison

- Compare within same `task_type`.
- Keep same model family when possible.
- Exclude extreme outliers if justified and documented.
- Require minimum sample size (recommended `n >= 20`) before claiming stable gains.

## Commands

If this toolkit is used in another project, point to the project-local data file:

```bash
export AOSO_DATA_FILE=.agent-loop-data/metrics/task-runs.csv
```

```bash
cd agent-auto-self-optimizing-closed-loop

# Log one task run
./scripts/log_task_run.sh \
  --task-id TASK-1001 \
  --task-type debug \
  --project core-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --total-tokens 1820 \
  --duration-sec 420 \
  --success true

# Overall + all skills
./scripts/metrics_report.sh --all

# Single skill effect
./scripts/metrics_report.sh --skill log-analysis-helper

# Pre/post engineering effect
./scripts/metrics_report.sh --all --cutover 2026-03-01
```
