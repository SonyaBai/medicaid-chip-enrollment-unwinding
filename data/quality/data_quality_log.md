# Data quality log: Medicaid and CHIP monthly enrollment

Source file: `state_medicaid_chip_applications_eligibility_enrollment.csv`
Cleaning rule: for each state and calendar month, keep the Updated (U) row when it exists; otherwise keep the Preliminary (P) row.
Numeric conversion: commas removed; blank, NA, N/A, and confidentiality code DS treated as missing.
Unwinding start used in flags: 2023-04 (CMS continuous coverage requirement ended March 31, 2023).

## Checks

| Check | Value | Detail |
| --- | ---: | --- |
| raw_row_count | 11,220 | Rows in downloaded CMS file |
| raw_column_count | 44 | Columns in downloaded CMS file |
| invalid_reporting_period | 0 | Rows whose Reporting Period could not be parsed as YYYYMM |
| state_month_keys | 5,661 | Distinct state-month combinations in the raw file |
| state_months_with_both_P_and_U | 5,559 | State-months that had both a Preliminary and an Updated row; Updated was kept |
| preferred_rows_updated | 5,610 | Preferred series rows that come from an Updated report |
| preferred_rows_preliminary_only | 51 | Preferred series rows that had only a Preliminary report |
| missing_total_enrollment | 2 | Preferred series rows missing Total Medicaid and CHIP Enrollment after numeric conversion |
| nonpositive_total_enrollment | 1 | Preferred series rows with total enrollment <= 0 |
| total_enrollment_footnotes | 527 | Preferred series rows with a CMS footnote on total Medicaid and CHIP enrollment |
| medicaid_plus_chip_not_equal_total | 0 | Preferred series rows where Medicaid + CHIP enrollment differs from the reported total by more than 1 person |
| duplicate_raw_state_period_version | 0 | Raw rows that share the same state, reporting period, and preliminary/updated flag |

## Notes for analysts

- National totals in this project are **sums of states with non-missing values** for that month, not a CMS-published national line.
- If a state is missing total enrollment in a month, it is excluded from that month's national sum and listed in SQL/output tables.
- Footnotes can mean a state included or excluded certain populations; read the footnote columns before interpreting a sharp change.
- DS (data suppressed) values, if present, were set to missing and are not imputed.
