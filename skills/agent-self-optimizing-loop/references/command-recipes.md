# Command Recipes

## 1) Initialize project data folder

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/setup_loop_workspace.sh" --workspace "$(pwd)"
```

## 2) Auto-run one full loop

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/auto_run_loop.sh" \
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

## 2b) Auto-run with telemetry from runtime env

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
CODEX_TOTAL_TOKENS=1820 \
CODEX_TASK_DURATION_SEC=420 \
"${SKILL_HOME}/scripts/auto_run_loop.sh" \
  --task-id TASK-1002 \
  --task-type debug \
  --project my-service \
  --model gpt-5 \
  --used-skill true \
  --skill-name log-analysis-helper \
  --success true \
  --enforce-telemetry
```

## 3) Log one task run (direct)

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

## 4) Measure skill effect

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/metrics_report.sh" --skill log-analysis-helper
```

## 5) Measure engineering pre/post effect

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/metrics_report.sh" --all --cutover 2026-03-01
```

## 6) Generate weekly review

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/weekly_review.sh"
```

## 7) Open the local dashboard

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/dashboard_server.sh" --host 127.0.0.1 --port 8765
```

## 8) Trigger optimization plan for one skill

```bash
SKILL_HOME="${CODEX_HOME:-$HOME/.codex}/skills/agent-self-optimizing-loop"
"${SKILL_HOME}/scripts/optimize_skill.sh" --skill log-analysis-helper
```
