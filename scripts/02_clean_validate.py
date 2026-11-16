#!/usr/bin/env python3
"""Clean and validate Medicaid/CHIP monthly enrollment data; write a data-quality log."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "state_medicaid_chip_applications_eligibility_enrollment.csv"
CLEAN_DIR = ROOT / "data" / "clean"
QA_DIR = ROOT / "data" / "quality"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)

# Continuous coverage requirement ended March 31, 2023; state unwinding began April 2023.
UNWINDING_START = pd.Period("2023-04", freq="M")
PRE_UNWINDING = pd.Period("2023-03", freq="M")

METRIC_COLS = [
    "Total Medicaid and CHIP Enrollment",
    "Total Medicaid Enrollment",
    "Total CHIP Enrollment",
    "Medicaid and CHIP Child Enrollment",
    "Total Adult Medicaid Enrollment",
]


def to_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    s = s.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NA": pd.NA, "N/A": pd.NA, "DS": pd.NA})
    s = s.str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def main() -> None:
    raw = pd.read_csv(RAW, dtype=str, low_memory=False)
    issues: list[dict] = []
    issues.append({"check": "raw_row_count", "value": int(len(raw)), "detail": "Rows in downloaded CMS file"})
    issues.append({"check": "raw_column_count", "value": int(raw.shape[1]), "detail": "Columns in downloaded CMS file"})

    df = raw.copy()
    df.columns = [c.strip() for c in df.columns]
    df["state"] = df["State Abbreviation"].str.strip()
    df["state_name"] = df["State Name"].str.strip()
    df["reporting_period"] = df["Reporting Period"].str.strip()
    df["period"] = pd.to_datetime(df["reporting_period"] + "01", format="%Y%m%d", errors="coerce")
    df["period_month"] = df["period"].dt.to_period("M")
    bad_period = df["period"].isna().sum()
    issues.append({"check": "invalid_reporting_period", "value": int(bad_period), "detail": "Rows whose Reporting Period could not be parsed as YYYYMM"})

    df["preliminary_or_updated"] = df["Preliminary or Updated"].str.strip().str.upper()
    df["final_report"] = df["Final Report"].str.strip().str.upper()
    df["expanded_medicaid"] = df["State Expanded Medicaid"].str.strip().str.upper()

    for col in METRIC_COLS:
        df[col + " (numeric)"] = to_numeric(df[col])
        footnote_col = col + " - footnotes"
        if footnote_col in df.columns:
            df[col + " footnote"] = df[footnote_col].fillna("").str.strip()
        else:
            df[col + " footnote"] = ""

    # Prefer Updated (U) over Preliminary (P) for the same state-month.
    df["_rank"] = df["preliminary_or_updated"].map({"U": 0, "P": 1}).fillna(2)
    df = df.sort_values(["state", "period_month", "_rank", "final_report"], ascending=[True, True, True, False])
    preferred = df.drop_duplicates(["state", "period_month"], keep="first").copy()

    n_raw_pairs = df.groupby(["state", "period_month"]).ngroups
    n_both = (df.groupby(["state", "period_month"])["preliminary_or_updated"].nunique() == 2).sum()
    n_pref_u = (preferred["preliminary_or_updated"] == "U").sum()
    n_pref_p = (preferred["preliminary_or_updated"] == "P").sum()
    issues.append({"check": "state_month_keys", "value": int(n_raw_pairs), "detail": "Distinct state-month combinations in the raw file"})
    issues.append({"check": "state_months_with_both_P_and_U", "value": int(n_both), "detail": "State-months that had both a Preliminary and an Updated row; Updated was kept"})
    issues.append({"check": "preferred_rows_updated", "value": int(n_pref_u), "detail": "Preferred series rows that come from an Updated report"})
    issues.append({"check": "preferred_rows_preliminary_only", "value": int(n_pref_p), "detail": "Preferred series rows that had only a Preliminary report"})

    total = preferred["Total Medicaid and CHIP Enrollment (numeric)"]
    issues.append({"check": "missing_total_enrollment", "value": int(total.isna().sum()), "detail": "Preferred series rows missing Total Medicaid and CHIP Enrollment after numeric conversion"})
    issues.append({"check": "nonpositive_total_enrollment", "value": int((total.fillna(0) <= 0).sum() - total.isna().sum()), "detail": "Preferred series rows with total enrollment <= 0"})
    issues.append({"check": "total_enrollment_footnotes", "value": int((preferred["Total Medicaid and CHIP Enrollment footnote"] != "").sum()), "detail": "Preferred series rows with a CMS footnote on total Medicaid and CHIP enrollment"})

    # Medicaid + CHIP vs reported total (allow small rounding differences)
    mcd = preferred["Total Medicaid Enrollment (numeric)"]
    chip = preferred["Total CHIP Enrollment (numeric)"]
    combo = mcd + chip
    abs_diff = (combo - total).abs()
    mismatch = preferred[(mcd.notna() & chip.notna() & total.notna()) & (abs_diff > 1)]
    issues.append({"check": "medicaid_plus_chip_not_equal_total", "value": int(len(mismatch)), "detail": "Preferred series rows where Medicaid + CHIP enrollment differs from the reported total by more than 1 person"})
    if len(mismatch):
        mismatch.assign(abs_diff=abs_diff).nlargest(15, "abs_diff")[
            ["state", "state_name", "reporting_period", "Total Medicaid Enrollment (numeric)", "Total CHIP Enrollment (numeric)", "Total Medicaid and CHIP Enrollment (numeric)"]
        ].to_csv(QA_DIR / "medicaid_chip_sum_mismatches.csv", index=False)

    # Duplicate raw keys
    raw_dups = raw.duplicated(["State Abbreviation", "Reporting Period", "Preliminary or Updated"], keep=False)
    issues.append({"check": "duplicate_raw_state_period_version", "value": int(raw_dups.sum()), "detail": "Raw rows that share the same state, reporting period, and preliminary/updated flag"})

    preferred = preferred.drop(columns=["_rank"])
    preferred["is_unwinding_or_after"] = preferred["period_month"] >= UNWINDING_START
    preferred["is_pre_unwinding_baseline"] = preferred["period_month"] == PRE_UNWINDING

    # Keep a compact analysis table
    keep_cols = [
        "state",
        "state_name",
        "reporting_period",
        "period",
        "period_month",
        "preliminary_or_updated",
        "final_report",
        "expanded_medicaid",
        "is_unwinding_or_after",
        "is_pre_unwinding_baseline",
    ]
    for col in METRIC_COLS:
        keep_cols += [col + " (numeric)", col + " footnote"]
    analysis = preferred[keep_cols].rename(columns={c + " (numeric)": c for c in METRIC_COLS})
    analysis.to_csv(CLEAN_DIR / "enrollment_preferred_series.csv", index=False)

    issues_df = pd.DataFrame(issues)
    issues_df.to_csv(QA_DIR / "data_quality_checks.csv", index=False)

    lines = [
        "# Data quality log: Medicaid and CHIP monthly enrollment",
        "",
        f"Source file: `{RAW.name}`",
        "Cleaning rule: for each state and calendar month, keep the Updated (U) row when it exists; otherwise keep the Preliminary (P) row.",
        "Numeric conversion: commas removed; blank, NA, N/A, and confidentiality code DS treated as missing.",
        f"Unwinding start used in flags: {UNWINDING_START} (CMS continuous coverage requirement ended March 31, 2023).",
        "",
        "## Checks",
        "",
        "| Check | Value | Detail |",
        "| --- | ---: | --- |",
    ]
    for row in issues:
        lines.append(f"| {row['check']} | {row['value']:,} | {row['detail']} |")
    lines += [
        "",
        "## Notes for analysts",
        "",
        "- National totals in this project are **sums of states with non-missing values** for that month, not a CMS-published national line.",
        "- If a state is missing total enrollment in a month, it is excluded from that month's national sum and listed in SQL/output tables.",
        "- Footnotes can mean a state included or excluded certain populations; read the footnote columns before interpreting a sharp change.",
        "- DS (data suppressed) values, if present, were set to missing and are not imputed.",
        "",
    ]
    (QA_DIR / "data_quality_log.md").write_text("\n".join(lines), encoding="utf-8")
    (QA_DIR / "clean_metadata.json").write_text(
        json.dumps({"preferred_rows": int(len(analysis)), "unwinding_start": str(UNWINDING_START), "baseline_month": str(PRE_UNWINDING)}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(analysis):,} preferred series rows and quality log to {QA_DIR}")


if __name__ == "__main__":
    main()
