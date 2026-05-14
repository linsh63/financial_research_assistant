#!/usr/bin/env bash
# 兼容入口：转发到 scripts/data/download_seed_dataset.sh。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/data/download_seed_dataset.sh" "$@"
