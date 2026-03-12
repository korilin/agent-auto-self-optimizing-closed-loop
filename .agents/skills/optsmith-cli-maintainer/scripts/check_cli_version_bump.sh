#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(git -C "${script_dir}" rev-parse --show-toplevel 2>/dev/null || (cd "${script_dir}/../../../.." && pwd))"
cd "${repo_root}"

version_files=(
  "pyproject.toml"
  "optsmith_cli/__init__.py"
  "Formula/optsmith.rb"
)

read_pyproject_version_stream() {
  awk -F'"' '
BEGIN { in_project = 0 }
/^\[project\]/ { in_project = 1; next }
/^\[/ && in_project { exit }
in_project && $1 ~ /^[[:space:]]*version[[:space:]]*=[[:space:]]*$/ { print $2; exit }
'
}

read_init_version_stream() {
  awk -F'"' '/^__version__[[:space:]]*=[[:space:]]*"/ { print $2; exit }'
}

read_formula_version_stream() {
  awk -F'"' '/^[[:space:]]*version[[:space:]]+"/ { print $2; exit }'
}

read_current_version() {
  local path="$1"
  case "${path}" in
    pyproject.toml) read_pyproject_version_stream < "${repo_root}/${path}" ;;
    optsmith_cli/__init__.py) read_init_version_stream < "${repo_root}/${path}" ;;
    Formula/optsmith.rb) read_formula_version_stream < "${repo_root}/${path}" ;;
    *) return 1 ;;
  esac
}

read_head_version() {
  local path="$1"
  if ! git cat-file -e "HEAD:${path}" >/dev/null 2>&1; then
    return 1
  fi
  case "${path}" in
    pyproject.toml) git show "HEAD:${path}" | read_pyproject_version_stream ;;
    optsmith_cli/__init__.py) git show "HEAD:${path}" | read_init_version_stream ;;
    Formula/optsmith.rb) git show "HEAD:${path}" | read_formula_version_stream ;;
    *) return 1 ;;
  esac
}

is_semver() {
  [[ "${1:-}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

version_gt() {
  local left="${1:-}"
  local right="${2:-}"
  local l1 l2 l3 r1 r2 r3
  IFS='.' read -r l1 l2 l3 <<<"${left}"
  IFS='.' read -r r1 r2 r3 <<<"${right}"

  if (( 10#${l1} > 10#${r1} )); then
    return 0
  fi
  if (( 10#${l1} < 10#${r1} )); then
    return 1
  fi
  if (( 10#${l2} > 10#${r2} )); then
    return 0
  fi
  if (( 10#${l2} < 10#${r2} )); then
    return 1
  fi
  if (( 10#${l3} > 10#${r3} )); then
    return 0
  fi
  return 1
}

is_cli_related_path() {
  local path="$1"
  case "${path}" in
    optsmith_cli/*|pyproject.toml|Formula/optsmith.rb) return 0 ;;
    *) return 1 ;;
  esac
}

has_head="true"
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  has_head="false"
fi

changed_files=()
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  changed_files+=("${line}")
done < <(
  {
    if [[ "${has_head}" == "true" ]]; then
      git diff --name-only HEAD --
    else
      git diff --name-only --
    fi
    git ls-files --others --exclude-standard
  } | awk 'NF' | sort -u
)

curr_pyproject="$(read_current_version "pyproject.toml" || true)"
curr_init="$(read_current_version "optsmith_cli/__init__.py" || true)"
curr_formula="$(read_current_version "Formula/optsmith.rb" || true)"

if [[ -z "${curr_pyproject}" || -z "${curr_init}" || -z "${curr_formula}" ]]; then
  echo "error: failed to parse current CLI version files"
  exit 1
fi

for v in "${curr_pyproject}" "${curr_init}" "${curr_formula}"; do
  if ! is_semver "${v}"; then
    echo "error: version must match semver x.y.z, got: ${v}"
    exit 1
  fi
done

if [[ "${curr_pyproject}" != "${curr_init}" || "${curr_pyproject}" != "${curr_formula}" ]]; then
  echo "error: version mismatch across files:"
  echo "  pyproject.toml: ${curr_pyproject}"
  echo "  optsmith_cli/__init__.py: ${curr_init}"
  echo "  Formula/optsmith.rb: ${curr_formula}"
  exit 1
fi

cli_changed="false"
for path in "${changed_files[@]-}"; do
  if is_cli_related_path "${path}"; then
    cli_changed="true"
    break
  fi
done

if [[ "${cli_changed}" != "true" ]]; then
  echo "CLI version check passed: no CLI-scope changes detected (current=${curr_pyproject})"
  exit 0
fi

missing_version_files=()
for f in "${version_files[@]}"; do
  if ! printf '%s\n' "${changed_files[@]-}" | grep -Fxq "${f}"; then
    missing_version_files+=("${f}")
  fi
done

if (( ${#missing_version_files[@]} > 0 )); then
  echo "error: CLI-scope changes detected but version files were not all updated:"
  printf '  - %s\n' "${missing_version_files[@]}"
  echo "required files:"
  printf '  - %s\n' "${version_files[@]}"
  exit 1
fi

if [[ "${has_head}" != "true" ]]; then
  echo "CLI version check passed: CLI changed and version files updated (initial commit, version=${curr_pyproject})"
  exit 0
fi

prev_pyproject="$(read_head_version "pyproject.toml" || true)"
prev_init="$(read_head_version "optsmith_cli/__init__.py" || true)"
prev_formula="$(read_head_version "Formula/optsmith.rb" || true)"

if [[ -z "${prev_pyproject}" || -z "${prev_init}" || -z "${prev_formula}" ]]; then
  echo "error: failed to parse previous HEAD version files"
  exit 1
fi

if [[ "${prev_pyproject}" != "${prev_init}" || "${prev_pyproject}" != "${prev_formula}" ]]; then
  echo "error: HEAD has inconsistent version values; fix before applying new CLI changes:"
  echo "  HEAD pyproject.toml: ${prev_pyproject}"
  echo "  HEAD optsmith_cli/__init__.py: ${prev_init}"
  echo "  HEAD Formula/optsmith.rb: ${prev_formula}"
  exit 1
fi

if [[ "${curr_pyproject}" == "${prev_pyproject}" ]]; then
  echo "error: CLI-scope changes detected but version was not bumped (still ${curr_pyproject})"
  exit 1
fi

if ! version_gt "${curr_pyproject}" "${prev_pyproject}"; then
  echo "error: version must increase (current=${curr_pyproject}, previous=${prev_pyproject})"
  exit 1
fi

echo "CLI version check passed: ${prev_pyproject} -> ${curr_pyproject}"
