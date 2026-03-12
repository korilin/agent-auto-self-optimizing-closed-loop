#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(git -C "${script_dir}" rev-parse --show-toplevel 2>/dev/null || (cd "${script_dir}/../../../.." && pwd))"
workflow_file="${repo_root}/.github/workflows/ci.yml"

if [[ ! -f "${workflow_file}" ]]; then
  echo "error: missing workflow file: ${workflow_file}"
  exit 1
fi

required_patterns=(
  "name: ci"
  "set -euxo pipefail"
  "ROOT_DATA=\"\${TMP_ROOT}/root-data\""
  "OPTSMITH_DATA_FILE=\"\${ROOT_DATA}/metrics/task-runs.csv\" ./scripts/log_task_run.sh"
  "OPTSMITH_KB_DIR=\"\${ROOT_DATA}/knowledge-base/errors\" OPTSMITH_REPORT_DIR=\"\${ROOT_DATA}/reports\" ./scripts/weekly_review.sh"
  ".agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh"
  ".agents/skills/optsmith-repo-maintainer/scripts/validate_repo_workflow.sh"
)

for pattern in "${required_patterns[@]}"; do
  if ! grep -Fq "${pattern}" "${workflow_file}"; then
    echo "error: workflow missing required pattern: ${pattern}"
    exit 1
  fi
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

root_data="${tmp_dir}/root-data"
mkdir -p "${root_data}/metrics" "${root_data}/knowledge-base/errors" "${root_data}/reports"

OPTSMITH_DATA_FILE="${root_data}/metrics/task-runs.csv" \
  "${repo_root}/scripts/log_task_run.sh" \
  --task-id "TASK-WF-CHECK-1" \
  --task-type "debug" \
  --model "gpt-5" \
  --used-skill "false" \
  --total-tokens "100" \
  --duration-sec "10" \
  --success "true" >/dev/null

OPTSMITH_KB_DIR="${root_data}/knowledge-base/errors" \
OPTSMITH_REPORT_DIR="${root_data}/reports" \
  "${repo_root}/scripts/weekly_review.sh" >/dev/null

OPTSMITH_DATA_FILE="${root_data}/metrics/task-runs.csv" \
  "${repo_root}/scripts/metrics_report.sh" --all >/dev/null

echo "workflow CI check passed"
