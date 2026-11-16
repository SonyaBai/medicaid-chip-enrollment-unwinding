-- Performance measures for Medicaid/CHIP monthly enrollment.
-- Baseline = March 2023 (last full month of the COVID-19 continuous coverage requirement).
-- National totals are the sum of states with non-missing Total Medicaid and CHIP Enrollment.

-- Monthly Colorado series
CREATE TABLE measure_colorado_monthly AS
SELECT
    reporting_period,
    period,
    preliminary_or_updated,
    "Total Medicaid and CHIP Enrollment" AS total_enrollment,
    "Total Medicaid Enrollment" AS medicaid_enrollment,
    "Total CHIP Enrollment" AS chip_enrollment,
    "Medicaid and CHIP Child Enrollment" AS child_enrollment,
    "Total Adult Medicaid Enrollment" AS adult_medicaid_enrollment
FROM enrollment
WHERE state = 'CO'
ORDER BY period;

-- Monthly national sums (states with usable total enrollment only)
CREATE TABLE measure_national_monthly AS
SELECT
    reporting_period,
    period,
    COUNT(*) AS states_with_total_enrollment,
    SUM("Total Medicaid and CHIP Enrollment") AS total_enrollment,
    SUM("Total Medicaid Enrollment") AS medicaid_enrollment,
    SUM("Total CHIP Enrollment") AS chip_enrollment,
    SUM("Medicaid and CHIP Child Enrollment") AS child_enrollment,
    SUM("Total Adult Medicaid Enrollment") AS adult_medicaid_enrollment
FROM enrollment
WHERE "Total Medicaid and CHIP Enrollment" IS NOT NULL
GROUP BY reporting_period, period
ORDER BY period;

-- March 2023 baseline by state
CREATE TABLE measure_state_baseline AS
SELECT
    state,
    state_name,
    "Total Medicaid and CHIP Enrollment" AS baseline_total_enrollment,
    "Total Medicaid Enrollment" AS baseline_medicaid,
    "Total CHIP Enrollment" AS baseline_chip
FROM enrollment
WHERE reporting_period = '202303'
  AND "Total Medicaid and CHIP Enrollment" IS NOT NULL;

-- Latest month available in the preferred series
CREATE TABLE measure_latest_month AS
SELECT MAX(reporting_period) AS latest_reporting_period
FROM enrollment
WHERE "Total Medicaid and CHIP Enrollment" IS NOT NULL;

-- State change from March 2023 to the latest month with data for that state
CREATE TABLE measure_state_change_to_latest AS
SELECT
    b.state,
    b.state_name,
    b.baseline_total_enrollment,
    e.reporting_period AS latest_reporting_period,
    e."Total Medicaid and CHIP Enrollment" AS latest_total_enrollment,
    e."Total Medicaid and CHIP Enrollment" - b.baseline_total_enrollment AS change_count,
    ROUND(100.0 * (e."Total Medicaid and CHIP Enrollment" - b.baseline_total_enrollment)
          / b.baseline_total_enrollment, 2) AS pct_change
FROM measure_state_baseline b
JOIN enrollment e
  ON e.state = b.state
JOIN measure_latest_month m
  ON e.reporting_period = m.latest_reporting_period
WHERE e."Total Medicaid and CHIP Enrollment" IS NOT NULL
ORDER BY pct_change;

-- Colorado change from March 2023 to each later month
CREATE TABLE measure_colorado_vs_baseline AS
SELECT
    c.reporting_period,
    c.period,
    c.total_enrollment,
    b.baseline_total_enrollment,
    c.total_enrollment - b.baseline_total_enrollment AS change_count,
    ROUND(100.0 * (c.total_enrollment - b.baseline_total_enrollment)
          / b.baseline_total_enrollment, 2) AS pct_change
FROM measure_colorado_monthly c
CROSS JOIN (SELECT baseline_total_enrollment FROM measure_state_baseline WHERE state = 'CO') b
ORDER BY c.period;

-- National change from March 2023
CREATE TABLE measure_national_vs_baseline AS
SELECT
    n.reporting_period,
    n.period,
    n.states_with_total_enrollment,
    n.total_enrollment,
    b.total_enrollment AS baseline_total_enrollment,
    n.total_enrollment - b.total_enrollment AS change_count,
    ROUND(100.0 * (n.total_enrollment - b.total_enrollment) / b.total_enrollment, 2) AS pct_change
FROM measure_national_monthly n
CROSS JOIN (SELECT total_enrollment FROM measure_national_monthly WHERE reporting_period = '202303') b
ORDER BY n.period;
