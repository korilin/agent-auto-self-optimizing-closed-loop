#!/usr/bin/env bash
set -euo pipefail

skill_src="$(cd "$(dirname "$0")/.." && pwd)"
codex_home="${CODEX_HOME:-$HOME/.codex}"
dest="${codex_home}/skills/aoso-repo-maintainer"
backup=""

mkdir -p "${codex_home}/skills"

if [[ -e "${dest}" ]]; then
  backup="${dest}.bak.$(date +%Y%m%d%H%M%S)"
  mv "${dest}" "${backup}"
fi

cp -R "${skill_src}" "${dest}"

echo "installed project-local skill:"
echo "  source: ${skill_src}"
echo "  dest:   ${dest}"
if [[ -n "${backup}" ]]; then
  echo "  backup: ${backup}"
fi
echo "restart Codex to ensure the updated skill metadata is loaded."
