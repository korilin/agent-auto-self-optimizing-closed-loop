#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

runtime_scripts=(
  "log_task_run.sh"
  "metrics_report.sh"
  "weekly_review.sh"
)

echo "[1/5] shell syntax checks"
bash -n "${repo_root}/scripts/create_skill.sh"
for f in "${runtime_scripts[@]}"; do
  bash -n "${repo_root}/scripts/${f}"
  bash -n "${repo_root}/skills/agent-self-optimizing-loop/scripts/${f}"
done
bash -n "${repo_root}/skills/agent-self-optimizing-loop/scripts/setup_loop_workspace.sh"
bash -n "${repo_root}/skills/aoso-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh"
bash -n "${repo_root}/skills/aoso-repo-maintainer/scripts/install_to_codex.sh"

echo "[2/5] runtime/script parity checks"
for f in "${runtime_scripts[@]}"; do
  cmp -s "${repo_root}/scripts/${f}" "${repo_root}/skills/agent-self-optimizing-loop/scripts/${f}" || {
    echo "error: runtime script out of sync: ${f}"
    echo "hint: run skills/aoso-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh"
    exit 1
  }
done

echo "[3/5] root toolkit smoke test"
mkdir -p "${tmp_dir}/rootdata/metrics" "${tmp_dir}/rootdata/knowledge-base/errors" "${tmp_dir}/rootdata/reports"
cp "${repo_root}/metrics/task-runs.csv" "${tmp_dir}/rootdata/metrics/task-runs.csv"
AOSO_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
  "${repo_root}/scripts/log_task_run.sh" \
  --task-id "TASK-ROOT-CHECK-1" \
  --task-type "debug" \
  --project "aoso" \
  --model "gpt-5" \
  --used-skill "false" \
  --total-tokens "100" \
  --duration-sec "10" \
  --success "true"
AOSO_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
  "${repo_root}/scripts/metrics_report.sh" --all >/dev/null
AOSO_KB_DIR="${tmp_dir}/rootdata/knowledge-base/errors" \
AOSO_REPORT_DIR="${tmp_dir}/rootdata/reports" \
  "${repo_root}/scripts/weekly_review.sh" >/dev/null

echo "[4/5] installable skill smoke test"
mkdir -p "${tmp_dir}/skill-project"
cd "${tmp_dir}/skill-project"
"${repo_root}/skills/agent-self-optimizing-loop/scripts/setup_loop_workspace.sh" --workspace "$(pwd)" >/dev/null
"${repo_root}/skills/agent-self-optimizing-loop/scripts/log_task_run.sh" \
  --task-id "TASK-SKILL-CHECK-1" \
  --task-type "debug" \
  --project "aoso" \
  --model "gpt-5" \
  --used-skill "false" \
  --total-tokens "120" \
  --duration-sec "12" \
  --success "true"
"${repo_root}/skills/agent-self-optimizing-loop/scripts/metrics_report.sh" --all >/dev/null
"${repo_root}/skills/agent-self-optimizing-loop/scripts/weekly_review.sh" >/dev/null
cd "${repo_root}"

echo "[5/5] done"
echo "repository workflow validation passed"
