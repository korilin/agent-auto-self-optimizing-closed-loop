#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(git -C "${script_dir}" rev-parse --show-toplevel 2>/dev/null || (cd "${script_dir}/../../../.." && pwd))"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

runtime_scripts=(
  "log_task_run.sh"
  "metrics_report.sh"
  "weekly_review.sh"
  "auto_run_loop.sh"
  "optimize_skill.sh"
  "dashboard_server.sh"
  "dashboard_server.py"
)

echo "[1/6] shell syntax checks"
bash -n "${repo_root}/scripts/create_skill.sh"
shell_runtime_scripts=(
  "log_task_run.sh"
  "metrics_report.sh"
  "weekly_review.sh"
  "auto_run_loop.sh"
  "optimize_skill.sh"
  "dashboard_server.sh"
)
for f in "${shell_runtime_scripts[@]}"; do
  bash -n "${repo_root}/scripts/${f}"
  bash -n "${repo_root}/skills/agent-optsmith-loop/scripts/${f}"
done
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/scripts/dashboard_server.py"
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/skills/agent-optsmith-loop/scripts/dashboard_server.py"
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/optsmith_cli/__init__.py"
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/optsmith_cli/cli.py"
PYTHONPATH="${repo_root}" python3 -m optsmith_cli.cli help >/dev/null
bash -n "${repo_root}/skills/agent-optsmith-loop/scripts/setup_loop_workspace.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/install_to_codex.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/check_readme_sync.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh"

echo "[2/6] runtime/script parity checks"
for f in "${runtime_scripts[@]}"; do
  cmp -s "${repo_root}/scripts/${f}" "${repo_root}/skills/agent-optsmith-loop/scripts/${f}" || {
    echo "error: runtime script out of sync: ${f}"
    echo "hint: run .agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh"
    exit 1
  }
done

echo "[3/6] README sync checks"
"${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/check_readme_sync.sh"

echo "[4/6] root toolkit smoke test"
mkdir -p "${tmp_dir}/rootdata/metrics" "${tmp_dir}/rootdata/knowledge-base/errors" "${tmp_dir}/rootdata/reports"
cp "${repo_root}/.agent-loop-data/metrics/task-runs.csv" "${tmp_dir}/rootdata/metrics/task-runs.csv"
OPTSMITH_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
  "${repo_root}/scripts/log_task_run.sh" \
  --task-id "TASK-ROOT-CHECK-1" \
  --task-type "debug" \
  --project "optsmith" \
  --model "gpt-5" \
  --used-skill "false" \
  --total-tokens "100" \
  --duration-sec "10" \
  --success "true"
OPTSMITH_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
  "${repo_root}/scripts/metrics_report.sh" --all >/dev/null
OPTSMITH_KB_DIR="${tmp_dir}/rootdata/knowledge-base/errors" \
OPTSMITH_REPORT_DIR="${tmp_dir}/rootdata/reports" \
  "${repo_root}/scripts/weekly_review.sh" >/dev/null
OPTSMITH_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
OPTSMITH_KB_DIR="${tmp_dir}/rootdata/knowledge-base/errors" \
OPTSMITH_REPORT_DIR="${tmp_dir}/rootdata/reports" \
  "${repo_root}/scripts/auto_run_loop.sh" \
  --task-id "TASK-ROOT-AUTO-1" \
  --task-type "ops" \
  --project "optsmith" \
  --model "gpt-5" \
  --used-skill "true" \
  --skill-name "agent-optsmith-loop" \
  --total-tokens "130" \
  --duration-sec "13" \
  --success "true" \
  --skip-weekly >/dev/null

mock_thread_id="019mock-telemetry-thread"
mock_codex_home="${tmp_dir}/mock-codex-home"
mock_session_dir="${mock_codex_home}/sessions/2026/03/09"
mkdir -p "${mock_session_dir}"
cat > "${mock_session_dir}/rollout-2026-03-09T12-00-00-${mock_thread_id}.jsonl" <<'EOF'
{"timestamp":"2026-03-09T12:00:00.000Z","type":"session_meta","payload":{"id":"019mock-telemetry-thread"}}
{"timestamp":"2026-03-09T12:01:00.000Z","type":"turn_context","payload":{"cwd":"/tmp/mock"}}
{"timestamp":"2026-03-09T12:01:20.000Z","type":"event_msg","payload":{"type":"token_count","info":{"last_token_usage":{"total_tokens":210}}}}
{"timestamp":"2026-03-09T12:02:05.000Z","type":"event_msg","payload":{"type":"token_count","info":{"last_token_usage":{"total_tokens":190}}}}
EOF

OPTSMITH_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
OPTSMITH_KB_DIR="${tmp_dir}/rootdata/knowledge-base/errors" \
OPTSMITH_REPORT_DIR="${tmp_dir}/rootdata/reports" \
CODEX_HOME="${mock_codex_home}" \
CODEX_THREAD_ID="${mock_thread_id}" \
  "${repo_root}/scripts/auto_run_loop.sh" \
  --task-id "TASK-ROOT-AUTO-TELEMETRY" \
  --task-type "ops" \
  --project "optsmith" \
  --model "gpt-5" \
  --used-skill "true" \
  --skill-name "agent-optsmith-loop" \
  --success "true" \
  --skip-weekly >/dev/null

last_row="$(tail -n 1 "${tmp_dir}/rootdata/metrics/task-runs.csv")"
logged_tokens="$(echo "${last_row}" | awk -F',' '{print $8}')"
logged_duration="$(echo "${last_row}" | awk -F',' '{print $9}')"
if [[ ! "${logged_tokens}" =~ ^[1-9][0-9]*$ ]]; then
  echo "error: telemetry fallback should resolve total_tokens > 0"
  echo "  row: ${last_row}"
  exit 1
fi
if [[ ! "${logged_duration}" =~ ^[1-9][0-9]*$ ]]; then
  echo "error: telemetry fallback should resolve duration_sec > 0"
  echo "  row: ${last_row}"
  exit 1
fi

OPTSMITH_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
OPTSMITH_KB_DIR="${tmp_dir}/rootdata/knowledge-base/errors" \
OPTSMITH_OPT_REPORT_DIR="${tmp_dir}/rootdata/reports/skill-optimization" \
  "${repo_root}/scripts/optimize_skill.sh" --skill "agent-optsmith-loop" >/dev/null
"${repo_root}/scripts/dashboard_server.sh" --host "127.0.0.1" --port "8876" >/dev/null 2>&1 &
dashboard_pid_root=$!
sleep 1
kill "${dashboard_pid_root}" >/dev/null 2>&1 || true

echo "[5/6] installable skill smoke test"
mkdir -p "${tmp_dir}/skill-project"
cd "${tmp_dir}/skill-project"
"${repo_root}/skills/agent-optsmith-loop/scripts/setup_loop_workspace.sh" --workspace "$(pwd)" >/dev/null
"${repo_root}/skills/agent-optsmith-loop/scripts/log_task_run.sh" \
  --task-id "TASK-SKILL-CHECK-1" \
  --task-type "debug" \
  --project "optsmith" \
  --model "gpt-5" \
  --used-skill "false" \
  --total-tokens "120" \
  --duration-sec "12" \
  --success "true"
"${repo_root}/skills/agent-optsmith-loop/scripts/metrics_report.sh" --all >/dev/null
"${repo_root}/skills/agent-optsmith-loop/scripts/weekly_review.sh" >/dev/null
"${repo_root}/skills/agent-optsmith-loop/scripts/auto_run_loop.sh" \
  --task-id "TASK-SKILL-AUTO-1" \
  --task-type "ops" \
  --project "optsmith" \
  --model "gpt-5" \
  --used-skill "true" \
  --skill-name "agent-optsmith-loop" \
  --total-tokens "140" \
  --duration-sec "14" \
  --success "true" \
  --skip-weekly >/dev/null
OPTSMITH_OPT_REPORT_DIR="${tmp_dir}/skill-project/.agent-loop-data/reports/skill-optimization" \
  "${repo_root}/skills/agent-optsmith-loop/scripts/optimize_skill.sh" --skill "agent-optsmith-loop" >/dev/null
"${repo_root}/skills/agent-optsmith-loop/scripts/dashboard_server.sh" --host "127.0.0.1" --port "8877" >/dev/null 2>&1 &
dashboard_pid_skill=$!
sleep 1
kill "${dashboard_pid_skill}" >/dev/null 2>&1 || true
cd "${repo_root}"

echo "[6/6] done"
echo "repository workflow validation passed"
