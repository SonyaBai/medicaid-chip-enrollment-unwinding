#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
echo "== 01 download =="
"$PY" scripts/01_download.py
echo "== 02 clean =="
"$PY" scripts/02_clean_validate.py
echo "== 03 sql =="
"$PY" scripts/03_sql_measures.py
echo "== 04 R =="
if command -v Rscript >/dev/null 2>&1; then
  Rscript scripts/04_analysis.R
else
  echo "WARNING: Rscript not found on PATH. Skipping R charts. Install R and rerun: Rscript scripts/04_analysis.R"
fi
echo "== 05 excel =="
"$PY" scripts/05_excel_report.py
echo "== 06 dashboard and PDF =="
"$PY" scripts/06_dashboard_and_pdf.py
echo "Done. See README.md, output/, and data/quality/."
