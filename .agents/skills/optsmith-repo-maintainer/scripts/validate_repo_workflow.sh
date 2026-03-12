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

echo "[1/9] shell syntax checks"
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
  bash -n "${repo_root}/skills/agent-optsmith/scripts/${f}"
done
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/scripts/dashboard_server.py"
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/skills/agent-optsmith/scripts/dashboard_server.py"
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/optsmith_cli/__init__.py"
PYTHONPYCACHEPREFIX="${tmp_dir}/pycache" python3 -m py_compile "${repo_root}/optsmith_cli/cli.py"
PYTHONPATH="${repo_root}" python3 -m optsmith_cli.cli help >/dev/null
bash -n "${repo_root}/skills/agent-optsmith/scripts/setup_loop_workspace.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/install_to_codex.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/check_readme_sync.sh"
bash -n "${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/auto_commit.sh"
bash -n "${repo_root}/.agents/skills/optsmith-cli-maintainer/scripts/check_cli_version_bump.sh"
bash -n "${repo_root}/.agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh"

echo "[2/9] runtime/script parity checks"
for f in "${runtime_scripts[@]}"; do
  cmp -s "${repo_root}/scripts/${f}" "${repo_root}/skills/agent-optsmith/scripts/${f}" || {
    echo "error: runtime script out of sync: ${f}"
    echo "hint: run .agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh"
    exit 1
  }
done

for f in "${runtime_scripts[@]}"; do
  cmp -s "${repo_root}/skills/agent-optsmith/scripts/${f}" "${repo_root}/optsmith_cli/resources/skills/agent-optsmith/scripts/${f}" || {
    echo "error: bundled CLI script out of sync: ${f}"
    echo "hint: run .agents/skills/optsmith-repo-maintainer/scripts/sync_runtime_to_installable_skill.sh"
    exit 1
  }
done

echo "[3/9] CLI version policy checks"
"${repo_root}/.agents/skills/optsmith-cli-maintainer/scripts/check_cli_version_bump.sh"

echo "[4/9] workflow policy checks"
"${repo_root}/.agents/skills/optsmith-workflow-maintainer/scripts/check_ci_workflow.sh"

echo "[5/9] README sync checks"
"${repo_root}/.agents/skills/optsmith-repo-maintainer/scripts/check_readme_sync.sh"

echo "[6/9] root toolkit smoke test"
mkdir -p "${tmp_dir}/rootdata/metrics" "${tmp_dir}/rootdata/knowledge-base/errors" "${tmp_dir}/rootdata/reports"
seed_csv="${repo_root}/.agents/optsmith-data/metrics/task-runs.csv"
if [[ ! -f "${seed_csv}" && -f "${repo_root}/.agent-loop-data/metrics/task-runs.csv" ]]; then
  seed_csv="${repo_root}/.agent-loop-data/metrics/task-runs.csv"
fi
if [[ -f "${seed_csv}" ]]; then
  cp "${seed_csv}" "${tmp_dir}/rootdata/metrics/task-runs.csv"
else
  echo "date,task_id,task_type,model,used_skill,skill_name,total_tokens,duration_sec,success,rework_count" > "${tmp_dir}/rootdata/metrics/task-runs.csv"
fi
OPTSMITH_DATA_FILE="${tmp_dir}/rootdata/metrics/task-runs.csv" \
  "${repo_root}/scripts/log_task_run.sh" \
  --task-id "TASK-ROOT-CHECK-1" \
  --task-type "debug" \
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
  --model "gpt-5" \
  --used-skill "true" \
  --skill-name "agent-optsmith" \
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
  --model "gpt-5" \
  --used-skill "true" \
  --skill-name "agent-optsmith" \
  --success "true" \
  --skip-weekly >/dev/null

last_row="$(tail -n 1 "${tmp_dir}/rootdata/metrics/task-runs.csv")"
logged_tokens="$(echo "${last_row}" | awk -F',' '{print $7}')"
logged_duration="$(echo "${last_row}" | awk -F',' '{print $8}')"
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
  "${repo_root}/scripts/optimize_skill.sh" --skill "agent-optsmith" >/dev/null
"${repo_root}/scripts/dashboard_server.sh" --host "127.0.0.1" --port "8876" >/dev/null 2>&1 &
dashboard_pid_root=$!
sleep 1
kill "${dashboard_pid_root}" >/dev/null 2>&1 || true

echo "[7/9] installable skill smoke test"
mkdir -p "${tmp_dir}/skill-project"
cd "${tmp_dir}/skill-project"
"${repo_root}/skills/agent-optsmith/scripts/setup_loop_workspace.sh" --workspace "$(pwd)" >/dev/null
"${repo_root}/skills/agent-optsmith/scripts/log_task_run.sh" \
  --task-id "TASK-SKILL-CHECK-1" \
  --task-type "debug" \
  --model "gpt-5" \
  --used-skill "false" \
  --total-tokens "120" \
  --duration-sec "12" \
  --success "true"
"${repo_root}/skills/agent-optsmith/scripts/metrics_report.sh" --all >/dev/null
"${repo_root}/skills/agent-optsmith/scripts/weekly_review.sh" >/dev/null
"${repo_root}/skills/agent-optsmith/scripts/auto_run_loop.sh" \
  --task-id "TASK-SKILL-AUTO-1" \
  --task-type "ops" \
  --model "gpt-5" \
  --used-skill "true" \
  --skill-name "agent-optsmith" \
  --total-tokens "140" \
  --duration-sec "14" \
  --success "true" \
  --skip-weekly >/dev/null
OPTSMITH_OPT_REPORT_DIR="${tmp_dir}/skill-project/.agents/optsmith-data/reports/skill-optimization" \
  "${repo_root}/skills/agent-optsmith/scripts/optimize_skill.sh" --skill "agent-optsmith" >/dev/null
"${repo_root}/skills/agent-optsmith/scripts/dashboard_server.sh" --host "127.0.0.1" --port "8877" >/dev/null 2>&1 &
dashboard_pid_skill=$!
sleep 1
kill "${dashboard_pid_skill}" >/dev/null 2>&1 || true
cd "${repo_root}"

echo "[8/9] CLI project install/update/uninstall smoke test"
mkdir -p "${tmp_dir}/cli-project"
PYTHONPATH="${repo_root}" python3 -m optsmith_cli.cli install \
  --workspace "${tmp_dir}/cli-project" \
  --skill-path ".agents/skills" \
  --data-dir ".agents/optsmith-data" >/dev/null

test -f "${tmp_dir}/cli-project/AGENTS.md"
test -d "${tmp_dir}/cli-project/.agents/skills/agent-optsmith"
test -f "${tmp_dir}/cli-project/.agents/optsmith-data/metrics/task-runs.csv"
grep -Eq 'skill_dir: `.agents/skills`|data_dir: `.agents/optsmith-data`' "${tmp_dir}/cli-project/AGENTS.md"

PYTHONPATH="${repo_root}" python3 -m optsmith_cli.cli update --workspace "${tmp_dir}/cli-project" >/dev/null
PYTHONPATH="${repo_root}" python3 -m optsmith_cli.cli uninstall --workspace "${tmp_dir}/cli-project" >/dev/null

if [[ -d "${tmp_dir}/cli-project/.agents/skills/agent-optsmith" ]]; then
  echo "error: uninstall should remove installed project skill"
  exit 1
fi
if [[ -d "${tmp_dir}/cli-project/.agents/optsmith-data" ]]; then
  echo "error: uninstall should remove data directory"
  exit 1
fi
if grep -q '<!-- OPTSMITH-SKILL:START -->' "${tmp_dir}/cli-project/AGENTS.md"; then
  echo "error: uninstall should remove OPTSMITH-SKILL managed block"
  exit 1
fi

echo "[9/9] done"
echo "repository workflow validation passed"
