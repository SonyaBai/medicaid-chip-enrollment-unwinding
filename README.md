# Medicaid and CHIP Enrollment Changes During the COVID-19 Continuous Coverage Unwinding, 2023–2026: Colorado and National Trends

A reproducible analysis of public CMS monthly Medicaid and CHIP enrollment for Colorado and the 50 states plus the District of Columbia. The project uses Python (pandas) for download, cleaning, and validation; SQL (SQLite) for performance measures; R (ggplot2) for statistical charts; Excel (openpyxl) for a stakeholder workbook; and an interactive HTML dashboard built with Plotly. The dashboard is intended to serve a similar role to a Power BI or Tableau view; this repository does **not** include a Power BI `.pbix` or Tableau `.twbx` file.

## Question

After the COVID-19 continuous coverage requirement ended on March 31, 2023, states resumed eligibility renewals (the “unwinding”). How did Medicaid and CHIP enrollment change in Colorado, and how does that change compare with other states, from March 2023 through the latest public CMS monthly report in this extract (July 2026)?

## Data sources

- **CMS, State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data**, on [data.medicaid.gov](https://data.medicaid.gov/dataset/6165f45b-ca93-5bb5-9d06-db29c692a360/). Dataset ID `6165f45b-ca93-5bb5-9d06-db29c692a360`.
- CSV used here: `https://data.medicaid.gov/api/1/datastore/query/6165f45b-ca93-5bb5-9d06-db29c692a360/0/download?format=csv`
- Retrieved on November 16, 2026 (America/Denver). The local copy is `data/raw/state_medicaid_chip_applications_eligibility_enrollment.csv` (11,220 rows, 44 columns).
- The file covers 51 geographies (50 states and the District of Columbia), with an isolated September 2013 month and then monthly reports from June 2017 through July 2026, including Preliminary (P) and Updated (U) versions of the same state-month.

Optional joins that were **not** used: CMS-64 / MBES expenditure data and Census population counts for per-capita rates. They were left out because this project stays with the enrollment performance-indicator file that could be downloaded and validated in full.

## Methods

1. **Download.** `scripts/01_download.py` retrieves the official CSV and writes `data/raw/source_metadata.txt`.
2. **Cleaning and validation (Python / pandas).** `scripts/02_clean_validate.py` builds a preferred monthly series: for each state and calendar month, the Updated (U) row is kept when it exists; otherwise the Preliminary (P) row is kept. Counts are converted to numbers (commas removed). Blanks and the confidentiality code `DS` are treated as missing and are not imputed. Flags mark the March 2023 baseline and months on or after April 2023. A data-quality log is written to `data/quality/`.
3. **Performance measures (SQL / SQLite).** `sql/enrollment_measures.sql`, executed by `scripts/03_sql_measures.py`, computes Colorado monthly enrollment, a national sum of states with non-missing totals, March 2023 baselines, and count and percent change to the latest common month (July 2026 in this extract).
4. **Charts (R / ggplot2).** `scripts/04_analysis.R` produces PNG charts and a numeric summary in `output/r_summary.txt`. Trend charts start in January 2020 so the pandemic rise and the unwinding are visible, and so a straight line is not drawn across the 2013–2017 reporting gap.
5. **Excel workbook.** `scripts/05_excel_report.py` writes `output/enrollment_summary.xlsx` with an overview sheet and filterable tables.
6. **Dashboard and stakeholder brief.** `scripts/06_dashboard_and_pdf.py` writes an interactive Plotly HTML dashboard and a one-page PDF (plus a markdown copy) for nontechnical readers.

## Assumptions

- March 2023 is the last full month of the continuous coverage requirement and is the baseline for percent change.
- “National” in this project means the **sum of the 51 states (including DC)** that reported a total for that month. It is not a separate CMS-published national line.
- Updated reports are preferred over Preliminary reports for the same state-month.
- Medicaid plus CHIP should match the reported combined total (in this extract, no preferred row differed by more than one person).
- Footnotes can change who is counted; they are documented but not used to adjust the published totals.

## Limitations

- This is not an official CMS or Colorado Department of Health Care Policy and Financing brief, and it is not a caseload forecast.
- **July 2026 figures are Preliminary for all 51 states.** Later Updated files may revise those totals.
- The public file has an isolated September 2013 month and then a gap until June 2017. Trend charts in this project start in January 2020 for that reason.
- Two preferred-series rows were missing a combined total: Connecticut and Maine in September 2013 (outside the unwinding window). Rhode Island reported a total of 0 for December 2024 with the footnote “Unable to Provide Data due to System Limitations.” That month is not imputed.
- 527 preferred-series rows have a CMS footnote on the combined total (for example, “includes individuals enrolled at any time in the month,” limited-benefit enrollees, or retroactive enrollments). Colorado’s combined total has one such footnote, in September 2025 (“Includes Retroactive Enrollments”).
- The “Total Adult Medicaid Enrollment” field is largely unpopulated before mid-2024, so adult Medicaid is not compared with the March 2023 baseline.
- Enrollment change has many causes (eligibility findings, transitions to other coverage, procedural disenrollment, births, new applications, and later data revisions). This analysis does not identify why any person gained or lost coverage and uses no personal health information.
- No per-capita adjustment and no expenditure (CMS-64 / MBES) join were performed.
- Territories are not in this file.

## Data-quality results (from the actual run)

| Check | Value |
| --- | ---: |
| Raw rows | 11,220 |
| Raw columns | 44 |
| Invalid reporting periods | 0 |
| Distinct state-month keys | 5,661 |
| State-months with both P and U (U kept) | 5,559 |
| Preferred rows from an Updated report | 5,610 |
| Preferred rows with only a Preliminary report | 51 |
| Missing combined totals | 2 (CT and ME, September 2013) |
| Non-positive combined totals | 1 (Rhode Island, December 2024, reported as 0) |
| Combined-total footnotes | 527 |
| Medicaid + CHIP ≠ reported total (difference > 1) | 0 |
| Duplicate raw state-period-version rows | 0 |

The full log is in `data/quality/data_quality_log.md`.

## Key findings (from the outputs of this run only)

All figures below come from the preferred series and the SQL measure tables in `output/tables/`. Percentages are rounded to one decimal place.

- **Colorado combined enrollment fell 30.4% from March 2023 to July 2026 (preliminary).** Enrollment went from 1,711,007 in March 2023 (Updated) to 1,190,986 in July 2026 (Preliminary), a decline of 520,021 people.
- **That decline was larger than the 51-state sum.** Combined enrollment across states with usable totals went from 94,363,487 in March 2023 (51 states) to 72,946,510 in July 2026 (51 states), a decline of 21,416,977 people, or **22.7%**.
- **Colorado ranked 11th of 51** in percent change from March 2023 to July 2026, where a rank of 1 is the largest decline. The median state change was −23.3%. The largest decline was Montana (−37.8%, from 329,804 to 205,223). The only increase was North Carolina (+15.1%, from 2,437,862 to 2,805,936), which had no combined-total footnote in those two months. This project does not estimate why North Carolina rose (Medicaid expansion and other policy or data factors are outside the scope of these tables).
- **In Colorado, Medicaid enrollment fell while CHIP rose.** Colorado Medicaid enrollment went from 1,591,111 in March 2023 to 1,055,616 in July 2026. Colorado CHIP enrollment went from 119,896 to 135,370 over the same period. Child (Medicaid and CHIP) enrollment in Colorado went from 653,060 to 525,759.
- **The same Medicaid-versus-CHIP pattern appears in the 51-state sum.** Medicaid enrollment fell from 87,190,897 to 65,742,057, while CHIP went from 7,172,590 to 7,204,453. Child enrollment fell from 42,276,078 to 34,894,015.
- **Colorado’s decline was already well underway in 2023–2024 and then leveled off.** Combined enrollment was 1,720,463 in April 2023 (slightly above the March baseline), 1,432,209 in December 2023, 1,176,823 in June 2024, and then stayed near 1.19–1.22 million through July 2026.
- **Every state’s July 2026 report in this extract is Preliminary**, so the latest point should be read as subject to later revision.

## How to reproduce

Python 3.10+ is required. R is required for the ggplot2 charts.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Install R (for example, from CRAN) and the packages dplyr, ggplot2, and readr.
# Then:
bash scripts/run_all.sh
```

Or run the steps one at a time from the project root:

```bash
python scripts/01_download.py
python scripts/02_clean_validate.py
python scripts/03_sql_measures.py
Rscript scripts/04_analysis.R
python scripts/05_excel_report.py
python scripts/06_dashboard_and_pdf.py
```

If the CMS download URL has changed, update `scripts/01_download.py` and `data/raw/source_metadata.txt`. The raw CSV already in `data/raw/` can be reused; you may start at step 02.

## Repository layout

- `scripts/` — download, cleaning, SQL runner, R charts, Excel, dashboard, and `run_all.sh`
- `sql/enrollment_measures.sql` — performance-measure queries
- `data/raw/`, `data/clean/`, `data/quality/`
- `output/tables/` — measure CSVs
- `output/charts/` — PNG charts (representative chart: `output/charts/02_pct_change_colorado_vs_national.png`)
- `output/enrollment_summary.xlsx` — Excel workbook
- `output/enrollment_dashboard.html` — interactive Plotly dashboard
- `output/enrollment_measures.sqlite` — SQLite database of measures
- `output/stakeholder_summary.pdf` and `STAKEHOLDER_SUMMARY.md` — one-page nontechnical brief

## License and use

Public CMS data. This project is an independent analysis for a professional portfolio. It is not affiliated with CMS or the State of Colorado and should not be cited as an official enrollment report.
