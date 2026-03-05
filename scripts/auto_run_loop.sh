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
total_tokens="${AOSO_TOTAL_TOKENS:-0}"
duration_sec="${AOSO_DURATION_SEC:-0}"
success="${AOSO_SUCCESS:-true}"
rework_count="${AOSO_REWORK_COUNT:-0}"
cutover="${AOSO_CUTOVER:-}"
run_weekly="true"

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

Description:
  Automatically run the self-optimizing loop:
  1) initialize workspace data in skill mode when missing
  2) log one task run
  3) run metrics reports
  4) run weekly review (unless --skip-weekly)
EOF
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
