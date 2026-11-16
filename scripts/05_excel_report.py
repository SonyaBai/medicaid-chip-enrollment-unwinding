#!/usr/bin/env python3
"""Write an Excel workbook of summary tables for stakeholders."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, numbers
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import LineChart, Reference, BarChart

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "output" / "tables"
OUT = ROOT / "output" / "enrollment_summary.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(bold=True, color="FFFFFF", name="Calibri")
TITLE_FONT = Font(bold=True, size=14, name="Calibri", color="1F4E79")
THIN = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)


def style_header(ws, row=1, start=1, end=None):
    end = end or ws.max_column
    for col in range(start, end + 1):
        cell = ws.cell(row, col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        cell.border = THIN


def autosize(ws, min_w=12, max_w=28):
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        length = max((len(str(c.value)) if c.value is not None else 0) for c in col)
        ws.column_dimensions[letter].width = min(max(length + 2, min_w), max_w)


def add_sheet(wb, name, df, title):
    ws = wb.create_sheet(name)
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(df.columns), 1))
    start = 3
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), start=start):
        for c_idx, value in enumerate(row, start=1):
            cell = ws.cell(r_idx, c_idx, value)
            cell.border = THIN
            cell.font = Font(name="Calibri")
            if isinstance(value, float) and abs(value) >= 1000:
                cell.number_format = "#,##0"
            elif isinstance(value, float):
                cell.number_format = "0.00"
            elif isinstance(value, int) and abs(value) >= 1000:
                cell.number_format = "#,##0"
    style_header(ws, row=start, end=len(df.columns))
    ws.row_dimensions[start].height = 30
    ws.auto_filter.ref = f"A{start}:{get_column_letter(len(df.columns))}{start + len(df)}"
    autosize(ws)
    ws.freeze_panes = f"A{start + 1}"
    return ws


def main() -> None:
    co = pd.read_csv(TABLES / "measure_colorado_vs_baseline.csv")
    nat = pd.read_csv(TABLES / "measure_national_vs_baseline.csv")
    chg = pd.read_csv(TABLES / "measure_state_change_to_latest.csv")
    co_m = pd.read_csv(TABLES / "measure_colorado_monthly.csv")

    wb = Workbook()
    # Overview
    ws = wb.active
    ws.title = "Overview"
    ws["A1"] = "Medicaid and CHIP enrollment during the continuous coverage unwinding"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:F1")
    ws["A2"] = "Source: CMS State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data (data.medicaid.gov). Baseline = March 2023."
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = 30

    co_base = co[co["reporting_period"].astype(str) == "202303"].iloc[0]
    co_last = co.sort_values("reporting_period").iloc[-1]
    nat_base = nat[nat["reporting_period"].astype(str) == "202303"].iloc[0]
    nat_last = nat.sort_values("reporting_period").iloc[-1]
    co_rank = int((chg["pct_change"] < chg.loc[chg["state"] == "CO", "pct_change"].values[0]).sum() + 1)

    rows = [
        ("Metric", "Value"),
        ("Colorado enrollment, March 2023", int(co_base["total_enrollment"])),
        (f"Colorado enrollment, {int(co_last['reporting_period'])}", int(co_last["total_enrollment"])),
        ("Colorado change (count)", int(co_last["change_count"])),
        ("Colorado change (percent)", float(co_last["pct_change"])),
        (f"Colorado rank by percent change among states (1 = largest decline) as of {int(co_last['reporting_period'])}", co_rank),
        (f"National sum, March 2023 ({int(nat_base['states_with_total_enrollment'])} states)", int(nat_base["total_enrollment"])),
        (f"National sum, {int(nat_last['reporting_period'])} ({int(nat_last['states_with_total_enrollment'])} states)", int(nat_last["total_enrollment"])),
        ("National sum change (percent)", float(nat_last["pct_change"])),
    ]
    for i, row in enumerate(rows, start=4):
        ws.cell(i, 1, row[0]).font = Font(bold=(i == 4), name="Calibri")
        cell = ws.cell(i, 2, row[1])
        cell.font = Font(name="Calibri", bold=(i == 4))
        if i == 4:
            ws.cell(i, 1).fill = HEADER_FILL
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            ws.cell(i, 1).font = HEADER_FONT
        if isinstance(row[1], int):
            cell.number_format = "#,##0"
        if isinstance(row[1], float):
            cell.number_format = "0.00"
    autosize(ws, min_w=20, max_w=80)

    add_sheet(wb, "Colorado monthly", co_m, "Colorado preferred monthly enrollment series")
    add_sheet(wb, "Colorado vs baseline", co, "Colorado enrollment versus March 2023 baseline")
    add_sheet(wb, "National monthly", nat, "Sum of reporting states versus March 2023 baseline")
    add_sheet(wb, "State change to latest", chg.sort_values("pct_change"), "State-level change from March 2023 to the latest common month")

    wb.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
