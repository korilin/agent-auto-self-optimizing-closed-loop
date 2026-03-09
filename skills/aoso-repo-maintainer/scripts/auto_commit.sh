#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
commit_message="chore(repo): automated workflow commit $(date +%Y-%m-%d)"
run_loop="true"
enforce_telemetry="false"
run_weekly="false"
run_push="true"

date_val="$(date +%Y-%m-%d)"
task_id="TASK-$(date +%Y%m%d-%H%M%S)"
task_type="${AOSO_TASK_TYPE:-repo-maintenance}"
project="${AOSO_PROJECT:-$(basename "${repo_root}")}"
model="${AOSO_MODEL:-gpt-5}"
used_skill="${AOSO_USED_SKILL:-true}"
skill_name="${AOSO_SKILL_NAME:-aoso-repo-maintainer}"
total_tokens="${AOSO_TOTAL_TOKENS:-}"
duration_sec="${AOSO_DURATION_SEC:-}"
success="${AOSO_SUCCESS:-true}"
rework_count="${AOSO_REWORK_COUNT:-0}"
cutover="${AOSO_CUTOVER:-}"

has_repo_changes() {
  if ! git diff --quiet; then
    return 0
  fi
  if ! git diff --cached --quiet; then
    return 0
  fi
  if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    return 0
  fi
  return 1
}

usage() {
  cat <<'EOF'
Usage:
  skills/aoso-repo-maintainer/scripts/auto_commit.sh [options]

Options:
  --message "<commit-message>"
  --skip-loop
  --enforce-telemetry
  --run-weekly
  --no-push
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

Description:
  1) Auto-run task logging + metrics before commit (default on)
  2) Stage all repository changes
  3) Create one commit non-interactively
  4) Push commit to remote branch (default on)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --message)
      commit_message="${2:-}"
      shift 2
      ;;
    --skip-loop)
      run_loop="false"
      shift
      ;;
    --enforce-telemetry)
      enforce_telemetry="true"
      shift
      ;;
    --run-weekly)
      run_weekly="true"
      shift
      ;;
    --no-push)
      run_push="false"
      shift
      ;;
    --task-id)
      task_id="${2:-}"
      shift 2
      ;;
    --task-type)
      task_type="${2:-}"
      shift 2
      ;;
    --project)
      project="${2:-}"
      shift 2
      ;;
    --model)
      model="${2:-}"
      shift 2
      ;;
    --used-skill)
      used_skill="${2:-}"
      shift 2
      ;;
    --skill-name)
      skill_name="${2:-}"
      shift 2
      ;;
    --total-tokens)
      total_tokens="${2:-}"
      shift 2
      ;;
    --duration-sec)
      duration_sec="${2:-}"
      shift 2
      ;;
    --success)
      success="${2:-}"
      shift 2
      ;;
    --rework-count)
      rework_count="${2:-}"
      shift 2
      ;;
    --date)
      date_val="${2:-}"
      shift 2
      ;;
    --cutover)
      cutover="${2:-}"
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

if [[ -z "${commit_message}" ]]; then
  echo "error: commit message must not be empty"
  exit 1
fi

cd "${repo_root}"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "error: not inside a git repository: ${repo_root}"
  exit 1
}

if ! has_repo_changes; then
  echo "no changes to commit"
  exit 0
fi

if [[ "${run_loop}" == "true" ]]; then
  loop_args=(
    --date "${date_val}"
    --task-id "${task_id}"
    --task-type "${task_type}"
    --project "${project}"
    --model "${model}"
    --used-skill "${used_skill}"
    --skill-name "${skill_name}"
    --success "${success}"
    --rework-count "${rework_count}"
  )
  if [[ -n "${total_tokens}" ]]; then
    loop_args+=(--total-tokens "${total_tokens}")
  fi
  if [[ -n "${duration_sec}" ]]; then
    loop_args+=(--duration-sec "${duration_sec}")
  fi
  if [[ -n "${cutover}" ]]; then
    loop_args+=(--cutover "${cutover}")
  fi
  if [[ "${run_weekly}" == "false" ]]; then
    loop_args+=(--skip-weekly)
  fi
  if [[ "${enforce_telemetry}" == "true" ]]; then
    loop_args+=(--enforce-telemetry)
  fi

  echo "running auto loop before commit..."
  "${repo_root}/scripts/auto_run_loop.sh" "${loop_args[@]}"
fi

git add -A

if git diff --cached --quiet; then
  echo "no changes to commit"
  exit 0
fi

echo "staged files:"
git diff --cached --name-only | sed 's/^/  - /'

git commit -m "${commit_message}"
echo "created commit: $(git rev-parse --short HEAD)"

if [[ "${run_push}" == "true" ]]; then
  echo "pushing commit to remote..."
  git push
  echo "push completed"
else
  echo "skip push: --no-push"
fi
