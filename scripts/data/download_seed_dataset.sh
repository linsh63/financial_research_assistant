#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p data/raw/new_energy data/raw/semiconductor data/raw/consumer

download_pdf() {
  local url="$1"
  local output="$2"

  if [[ -s "$output" ]]; then
    echo "skip: $output"
    return
  fi

  echo "download: $output"
  curl -L --fail --retry 2 --connect-timeout 20 -o "$output" "$url"
}

download_pdf \
  "https://static.cninfo.com.cn/finalpage/2025-03-25/1222881496.PDF" \
  "data/raw/new_energy/byd_2024_annual_report.pdf"

download_pdf \
  "https://static.cninfo.com.cn/finalpage/2025-03-15/1222806982.PDF" \
  "data/raw/new_energy/catl_2024_annual_report.pdf"

download_pdf \
  "https://static.cninfo.com.cn/finalpage/2024-08-30/1221050804.PDF" \
  "data/raw/semiconductor/smic_2024_half_year_report.pdf"

download_pdf \
  "https://static.cninfo.com.cn/finalpage/2026-04-17/1225114741.PDF" \
  "data/raw/consumer/moutai_2025_annual_report.pdf"

download_pdf \
  "https://static.cninfo.com.cn/finalpage/2026-03-31/1225065145.PDF" \
  "data/raw/consumer/midea_2025_annual_report.pdf"

download_pdf \
  "https://static.cninfo.com.cn/finalpage/2024-08-30/1221059362.PDF" \
  "data/raw/consumer/haitian_flavouring_2024_half_year_announcement.pdf"

echo "done"
find data/raw -name "*.pdf" -type f | sort
