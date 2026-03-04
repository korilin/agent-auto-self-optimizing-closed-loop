# Command Recipes

## 1) Initialize project data folder

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/setup_loop_workspace.sh" --workspace "$(pwd)"
```

## 2) Log one task run

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

## 3) Measure skill effect

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/metrics_report.sh" --skill log-analysis-helper
```

## 4) Measure engineering pre/post effect

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/metrics_report.sh" --all --cutover 2026-03-01
```

## 5) Generate weekly review

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/weekly_review.sh"
```
