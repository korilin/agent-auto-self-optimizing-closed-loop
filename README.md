# Agent Auto Self-Optimizing Closed Loop

[中文说明（README_CN）](README_CN.md)

A practical template to let an AI coding agent optimize itself over time with:

- Governance rules in `AGENTS.md`
- Auto skill scaffolding via scripts
- Error knowledge base templates
- Weekly review and feedback loop
- Measurable token and productivity impact tracking

## Repository Layout

- `AGENTS.md`: Runtime governance and quality gates.
- `docs/closed-loop-playbook.md`: Daily and weekly operating playbook.
- `docs/measurement-framework.md`: How to quantify token and efficiency gains.
- `scripts/create_skill.sh`: Create a skill skeleton with normalized naming.
- `scripts/weekly_review.sh`: Generate a weekly optimization report from error KB.
- `scripts/log_task_run.sh`: Append one standardized task-run record to metrics CSV.
- `scripts/metrics_report.sh`: Compute overall, per-skill, and pre/post impact metrics.
- `metrics/task-runs.csv`: Task execution dataset for impact analysis.
- `templates/skill/SKILL.md.template`: Minimal skill template.
- `templates/knowledge-base/error-entry.md`: Error record template.
- `templates/reports/weekly-self-optimization-report.md`: Weekly report template.
- `knowledge-base/errors/`: Error entries (one file per incident).
- `reports/`: Generated weekly reports.

## Quick Start

```bash
git clone git@github.com:<user>/agent-auto-self-optimizing-closed-loop.git
cd agent-auto-self-optimizing-closed-loop

# 1) Create a new skill scaffold
./scripts/create_skill.sh log-analysis-helper

# 2) Add error entries under knowledge-base/errors/
# Use templates/knowledge-base/error-entry.md as source.

# 3) Generate weekly report
./scripts/weekly_review.sh

# 4) Check optimization effect
./scripts/metrics_report.sh --all

# 5) Record one task run
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
```

## Recommended Workflow

1. Keep `AGENTS.md` short and strict; update it only with validated rules.
2. Create or update skills when the same task repeats frequently.
3. Log every failure in the error KB with root cause and prevention.
4. Run weekly review and promote proven prevention rules into `AGENTS.md` or skills.
5. Log task runs in `metrics/task-runs.csv` and track measurable gains.

## Publish Checklist

1. Initialize git and create initial commit.
2. Verify scripts run locally.
3. Add remote: `git@github.com:<user>/agent-auto-self-optimizing-closed-loop.git`
4. Push `main`.
