#!/usr/bin/env bash
set -euo pipefail

workspace_dir="${AOSO_WORKSPACE_DIR:-$(pwd)}"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/setup_loop_workspace.sh [--workspace <path>]

Description:
  Initialize self-optimization data directories for the target project.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      workspace_dir="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${workspace_dir}" ]]; then
  echo "error: workspace path is empty"
  exit 1
fi

workspace_dir="$(cd "${workspace_dir}" && pwd)"

data_root="${AOSO_DATA_ROOT:-${workspace_dir}/.agent-loop-data}"
metrics_file="${AOSO_DATA_FILE:-${data_root}/metrics/task-runs.csv}"
kb_dir="${AOSO_KB_DIR:-${data_root}/knowledge-base/errors}"
report_dir="${AOSO_REPORT_DIR:-${data_root}/reports}"
skills_dir="${data_root}/skills"
templates_dir="${data_root}/templates"
error_template="${templates_dir}/error-entry.md"

mkdir -p "$(dirname "${metrics_file}")" "${kb_dir}" "${report_dir}" "${skills_dir}" "${templates_dir}"

if [[ ! -f "${metrics_file}" ]]; then
  echo "date,task_id,task_type,project,model,used_skill,skill_name,total_tokens,duration_sec,success,rework_count" > "${metrics_file}"
fi

if [[ ! -f "${error_template}" ]]; then
  cat > "${error_template}" <<'EOF'
---
date: YYYY-MM-DD
task_type: coding|debug|review|docs|ops
severity: P0|P1|P2|P3
status: open|closed
root_cause: TODO
prevention_rule: TODO
trigger_signals: TODO
token_cost_estimate: 0
---

# Symptom

Describe what failed and how it was observed.

# Root Cause

Single primary cause. Keep it specific and testable.

# Fix Applied

Describe the exact change that resolved the issue.

# Prevention Rule

Rule to add to AGENTS or a skill so this does not repeat.

# Trigger Signals

List early warning signs that should trigger the prevention rule.

# Verification

Tests/checks used to confirm the fix.
EOF
fi

echo "initialized self-optimization workspace:"
echo "  workspace: ${workspace_dir}"
echo "  data_root: ${data_root}"
echo "  metrics_file: ${metrics_file}"
echo "  kb_dir: ${kb_dir}"
echo "  report_dir: ${report_dir}"
echo "  local_skills_dir: ${skills_dir}"
echo "  error_template: ${error_template}"
