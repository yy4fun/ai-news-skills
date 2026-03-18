#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${HOME}/.openclaw/workspace/skills"

mkdir -p "${TARGET_DIR}"

install_skill() {
  local skill_name="$1"
  local src="${SCRIPT_DIR}/skills/${skill_name}"
  local dst="${TARGET_DIR}/${skill_name}"

  if [[ ! -d "${src}" ]]; then
    echo "Missing skill directory: ${src}" >&2
    exit 1
  fi

  rm -rf "${dst}"
  cp -R "${src}" "${dst}"
  echo "Installed ${skill_name} -> ${dst}"
}

install_skill "ai_news_fetcher"
install_skill "ai_news_reporter"

echo
echo "Done."
echo "Next:"
echo "1. Copy bitable_target.example.json to bitable_target.json for each skill"
echo "2. Fill in your own Feishu app/table configuration"
