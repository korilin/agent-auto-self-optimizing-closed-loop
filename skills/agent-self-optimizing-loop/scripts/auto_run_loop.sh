#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "${SCRIPT_DIR}/../SKILL.md" ]]; then
  mode="skill"
  workspace_dir="${AOSO_WORKSPACE_DIR:-$(pwd)}"
  workspace_dir="$(cd "${workspace_dir}" && pwd)"
  setup_script="${SCRIPT_DIR}/setup_loop_workspace.sh"
else
  mode="root"
  root_dir="$(cd "${SCRIPT_DIR}/.." && pwd)"
  workspace_dir="${AOSO_WORKSPACE_DIR:-${root_dir}}"
  setup_script=""
fi

date_val="$(date +%Y-%m-%d)"
task_id="TASK-$(date +%Y%m%d-%H%M%S)"
task_type="${AOSO_TASK_TYPE:-coding}"
project="${AOSO_PROJECT:-$(basename "${workspace_dir}")}"
model="${AOSO_MODEL:-gpt-5}"
used_skill="${AOSO_USED_SKILL:-true}"
skill_name="${AOSO_SKILL_NAME:-agent-self-optimizing-loop}"
total_tokens="${AOSO_TOTAL_TOKENS:-}"
duration_sec="${AOSO_DURATION_SEC:-}"
success="${AOSO_SUCCESS:-true}"
rework_count="${AOSO_REWORK_COUNT:-0}"
cutover="${AOSO_CUTOVER:-}"
run_weekly="true"
enforce_telemetry="false"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/auto_run_loop.sh [options]

Options:
  --task-id <id>
  --task-type <type>
  --project <name>
  --model <name>
  --used-skill <true|false>
  --skill-name <name>
  --total-tokens <int>=0
  --duration-sec <int>=0
  --success <true|false>
  --rework-count <int>=0
  --date <YYYY-MM-DD>
  --cutover <YYYY-MM-DD>
  --skip-weekly
  --enforce-telemetry

Description:
  Automatically run the self-optimizing loop:
  1) initialize workspace data in skill mode when missing
  2) log one task run
  3) run metrics reports
  4) run weekly review (unless --skip-weekly)

Telemetry values are resolved in this order:
  - explicit CLI args (--total-tokens / --duration-sec)
  - env overrides:
      tokens: AOSO_TOTAL_TOKENS, CODEX_TOTAL_TOKENS, OPENAI_TOTAL_TOKENS, TASK_TOTAL_TOKENS
      duration: AOSO_DURATION_SEC, CODEX_TASK_DURATION_SEC, TASK_DURATION_SEC
  - fallback duration from task start timestamp:
      AOSO_TASK_START_TS or TASK_START_TS (unix epoch seconds)
  - final fallback: 0
EOF
}

first_non_empty() {
  for value in "$@"; do
    if [[ -n "${value}" ]]; then
      printf '%s' "${value}"
      return 0
    fi
  done
  return 1
}

resolve_duration_from_start_ts() {
  local start_ts="$1"
  if [[ ! "${start_ts}" =~ ^[0-9]+$ ]]; then
    return 1
  fi
  local now_ts
  now_ts="$(date +%s)"
  if [[ "${now_ts}" -lt "${start_ts}" ]]; then
    return 1
  fi
  printf '%s' "$((now_ts - start_ts))"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-id) task_id="${2:-}"; shift 2 ;;
    --task-type) task_type="${2:-}"; shift 2 ;;
    --project) project="${2:-}"; shift 2 ;;
    --model) model="${2:-}"; shift 2 ;;
    --used-skill) used_skill="${2:-}"; shift 2 ;;
    --skill-name) skill_name="${2:-}"; shift 2 ;;
    --total-tokens) total_tokens="${2:-}"; shift 2 ;;
    --duration-sec) duration_sec="${2:-}"; shift 2 ;;
    --success) success="${2:-}"; shift 2 ;;
    --rework-count) rework_count="${2:-}"; shift 2 ;;
    --date) date_val="${2:-}"; shift 2 ;;
    --cutover) cutover="${2:-}"; shift 2 ;;
    --skip-weekly) run_weekly="false"; shift ;;
    --enforce-telemetry) enforce_telemetry="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "${mode}" == "skill" && ! -d "${workspace_dir}/.agent-loop-data" ]]; then
  "${setup_script}" --workspace "${workspace_dir}" >/dev/null
fi

if [[ -z "${task_id}" ]]; then
  echo "error: --task-id must not be empty"
  exit 1
fi

if [[ "${used_skill}" == "false" ]]; then
  skill_name=""
fi

if [[ -z "${total_tokens}" ]]; then
  total_tokens="$(first_non_empty \
    "${AOSO_TOTAL_TOKENS:-}" \
    "${CODEX_TOTAL_TOKENS:-}" \
    "${OPENAI_TOTAL_TOKENS:-}" \
    "${TASK_TOTAL_TOKENS:-}" || true)"
fi

if [[ -z "${duration_sec}" ]]; then
  duration_sec="$(first_non_empty \
    "${AOSO_DURATION_SEC:-}" \
    "${CODEX_TASK_DURATION_SEC:-}" \
    "${TASK_DURATION_SEC:-}" || true)"
fi

if [[ -z "${duration_sec}" ]]; then
  duration_sec="$(resolve_duration_from_start_ts "$(first_non_empty \
    "${AOSO_TASK_START_TS:-}" \
    "${TASK_START_TS:-}" || true)" || true)"
fi

if [[ -z "${total_tokens}" ]]; then
  total_tokens="0"
fi
if [[ -z "${duration_sec}" ]]; then
  duration_sec="0"
fi

if [[ ! "${total_tokens}" =~ ^[0-9]+$ ]]; then
  echo "error: resolved total_tokens is not an integer: ${total_tokens}"
  exit 1
fi
if [[ ! "${duration_sec}" =~ ^[0-9]+$ ]]; then
  echo "error: resolved duration_sec is not an integer: ${duration_sec}"
  exit 1
fi

if [[ "${enforce_telemetry}" == "true" && ( "${total_tokens}" == "0" || "${duration_sec}" == "0" ) ]]; then
  echo "error: telemetry missing while --enforce-telemetry is enabled"
  echo "hint: pass --total-tokens/--duration-sec or set telemetry env vars"
  exit 1
fi

if [[ "${total_tokens}" == "0" || "${duration_sec}" == "0" ]]; then
  echo "warning: telemetry incomplete (total_tokens=${total_tokens}, duration_sec=${duration_sec})"
fi

metrics_args=(--all)
if [[ -n "${cutover}" ]]; then
  metrics_args+=(--cutover "${cutover}")
fi

skill_metrics_args=(--skill "${skill_name}")
if [[ -n "${cutover}" ]]; then
  skill_metrics_args+=(--cutover "${cutover}")
fi

echo "[1/4] logging task run"
"${SCRIPT_DIR}/log_task_run.sh" \
  --date "${date_val}" \
  --task-id "${task_id}" \
  --task-type "${task_type}" \
  --project "${project}" \
  --model "${model}" \
  --used-skill "${used_skill}" \
  --skill-name "${skill_name}" \
  --total-tokens "${total_tokens}" \
  --duration-sec "${duration_sec}" \
  --success "${success}" \
  --rework-count "${rework_count}"

echo "[2/4] running overall metrics"
"${SCRIPT_DIR}/metrics_report.sh" "${metrics_args[@]}"

echo "[3/4] running skill metrics"
if [[ "${used_skill}" == "true" && -n "${skill_name}" ]]; then
  "${SCRIPT_DIR}/metrics_report.sh" "${skill_metrics_args[@]}"
else
  echo "skipped: no skill row for this run"
fi

echo "[4/4] running weekly review"
if [[ "${run_weekly}" == "true" ]]; then
  "${SCRIPT_DIR}/weekly_review.sh"
else
  echo "skipped: --skip-weekly"
fi

echo "auto loop run completed"
