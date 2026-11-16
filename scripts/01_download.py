#!/usr/bin/env python3
"""Download CMS State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data."""
from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

DATASET_ID = "6165f45b-ca93-5bb5-9d06-db29c692a360"
DATASET_PAGE = f"https://data.medicaid.gov/dataset/{DATASET_ID}/"
DOWNLOAD_URL = f"https://data.medicaid.gov/api/1/datastore/query/{DATASET_ID}/0/download?format=csv"
OUT = RAW / "state_medicaid_chip_applications_eligibility_enrollment.csv"
META = RAW / "source_metadata.txt"


def main() -> None:
    print(f"Downloading enrollment file from:\n  {DOWNLOAD_URL}")
    with requests.get(DOWNLOAD_URL, stream=True, timeout=180) as r:
        r.raise_for_status()
        tmp = OUT.with_suffix(".csv.part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
        tmp.replace(OUT)
    size = OUT.stat().st_size
    print(f"Saved {OUT} ({size:,} bytes)")
    META.write_text(
        "Dataset: State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data\n"
        f"Dataset page: {DATASET_PAGE}\n"
        f"Download URL: {DOWNLOAD_URL}\n"
        "Publisher: Centers for Medicare & Medicaid Services (CMS), data.medicaid.gov\n"
        "Methodology: https://www.medicaid.gov/medicaid/national-medicaid-chip-program-information/medicaid-chip-enrollment-data/monthly-medicaid-chip-application-eligibility-determination-and-enrollment-reports-data\n"
        f"Local file size (bytes): {size}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
