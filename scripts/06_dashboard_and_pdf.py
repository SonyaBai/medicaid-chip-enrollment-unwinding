#!/usr/bin/env python3
"""Interactive Plotly HTML dashboard and a one-page nontechnical PDF summary."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "output" / "tables"
OUT = ROOT / "output"
CHARTS = OUT / "charts"


def period_label(yyyymm) -> str:
    s = str(int(yyyymm))
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    return f"{months[int(s[4:6]) - 1]} {s[:4]}"


def build_dashboard(co, nat, chg) -> None:
    co = co.copy()
    nat = nat.copy()
    co["date"] = pd.to_datetime(co["period"])
    nat["date"] = pd.to_datetime(nat["period"])
    # Avoid a straight line across the 2013-09 to 2017-06 reporting gap.
    co = co[co["date"] >= "2020-01-01"].copy()
    nat = nat[nat["date"] >= "2020-01-01"].copy()
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Colorado enrollment (count)",
            "Percent change since March 2023",
            "State percent change, March 2023 to latest month",
            "Colorado vs. national percent change (same baseline)",
        ),
        specs=[[{"type": "xy"}, {"type": "xy"}], [{"type": "xy"}, {"type": "xy"}]],
        vertical_spacing=0.16,
        horizontal_spacing=0.10,
    )
    fig.add_trace(
        go.Scatter(x=co["date"], y=co["total_enrollment"], name="Colorado enrollment", line=dict(color="#1f4e79", width=2)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=co["date"], y=co["pct_change"], name="Colorado % change", line=dict(color="#1f4e79", width=2)),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(x=nat["date"], y=nat["pct_change"], name="Sum of states % change", line=dict(color="#7b2d8e", width=2)),
        row=1, col=2,
    )
    chg_sorted = chg.sort_values("pct_change")
    colors = ["#c0504d" if s == "CO" else "#1f4e79" for s in chg_sorted["state"]]
    fig.add_trace(
        go.Bar(x=chg_sorted["pct_change"], y=chg_sorted["state"], orientation="h", marker_color=colors, name="State % change", showlegend=False),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(x=co["date"], y=co["pct_change"], name="Colorado", line=dict(color="#1f4e79", width=2), showlegend=False),
        row=2, col=2,
    )
    fig.add_trace(
        go.Scatter(x=nat["date"], y=nat["pct_change"], name="Sum of reporting states", line=dict(color="#7b2d8e", width=2), showlegend=False),
        row=2, col=2,
    )
    fig.add_vline(x=pd.Timestamp("2023-04-01"), line_dash="dash", line_color="gray", row=1, col=1)
    fig.update_layout(
        title="Medicaid and CHIP enrollment during the continuous coverage unwinding (interactive dashboard)",
        height=900,
        template="plotly_white",
        legend=dict(orientation="h", y=1.08),
        annotations=list(fig.layout.annotations) + [
            dict(
                text="Interactive HTML dashboard built with Plotly (not a Power BI .pbix or Tableau .twbx file). Dashed line marks April 2023, when unwinding began.",
                xref="paper", yref="paper", x=0, y=-0.08, showarrow=False, font=dict(size=11, color="#555"),
            )
        ],
        margin=dict(b=80),
    )
    fig.update_yaxes(title_text="Enrollees", row=1, col=1, tickformat=",")
    fig.update_yaxes(title_text="Percent change", row=1, col=2)
    fig.update_xaxes(title_text="Percent change", row=2, col=1)
    fig.update_yaxes(title_text="State", row=2, col=1, tickfont=dict(size=8))
    fig.update_yaxes(title_text="Percent change", row=2, col=2)
    out = OUT / "enrollment_dashboard.html"
    fig.write_html(out, include_plotlyjs=True)
    print(f"Wrote {out}")


class LetterPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 8, "One-page stakeholder summary  |  Public CMS enrollment data  |  Not official CMS analysis", align="C")


def build_pdf(co, nat, chg) -> None:
    co_base = co[co["reporting_period"] == 202303].iloc[0] if (co["reporting_period"] == 202303).any() else co[co["reporting_period"] == "202303"].iloc[0]
    # reporting_period may be int or str
    def row_for(df, period):
        s = df["reporting_period"].astype(str)
        return df[s == str(period)].iloc[0]

    co_base = row_for(co, "202303")
    co_last = co.sort_values("reporting_period").iloc[-1]
    nat_base = row_for(nat, "202303")
    nat_last = nat.sort_values("reporting_period").iloc[-1]
    co_pct = float(co_last["pct_change"])
    nat_pct = float(nat_last["pct_change"])
    co_rank = int((chg["pct_change"] < chg.loc[chg["state"].astype(str) == "CO", "pct_change"].values[0]).sum() + 1)
    n_states = int(chg["state"].nunique())
    last_label = period_label(co_last["reporting_period"])

    def fmt(n):
        return f"{int(round(n)):,}"

    pdf = LetterPDF(format="Letter", unit="mm")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_fill_color(31, 78, 121)
    pdf.rect(0, 0, 216, 22, "F")
    pdf.set_xy(15, 6)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 6, "Medicaid and CHIP Enrollment During the Unwinding Period", ln=1)
    pdf.set_x(15)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, "A one-page briefing for nontechnical stakeholders  |  Colorado focus, with national comparison")

    pdf.set_text_color(30, 30, 30)
    pdf.set_xy(15, 28)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "The question", ln=1)
    pdf.set_font("Helvetica", size=10)
    pdf.set_x(15)
    pdf.multi_cell(180, 5, "After the COVID-19 continuous coverage requirement ended on March 31, 2023, states resumed eligibility renewals (the \"unwinding\"). How did Medicaid and CHIP enrollment change in Colorado and across states from March 2023 through the latest public CMS monthly report?")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(15)
    pdf.cell(0, 7, "What the public data show", ln=1)
    pdf.set_font("Helvetica", size=10)
    bullets = [
        f"In March 2023, Colorado reported {fmt(co_base['total_enrollment'])} people enrolled in Medicaid and CHIP. By {last_label}, that figure was {fmt(co_last['total_enrollment'])}, a change of {fmt(co_last['change_count'])} people, or {co_pct:.1f}%.",
        f"Across states with usable data, combined enrollment went from {fmt(nat_base['total_enrollment'])} in March 2023 ({int(nat_base['states_with_total_enrollment'])} states) to {fmt(nat_last['total_enrollment'])} in {last_label} ({int(nat_last['states_with_total_enrollment'])} states), a change of {nat_pct:.1f}%.",
        f"Among {n_states} states with both a March 2023 baseline and a {last_label} total, Colorado ranked {co_rank} in percent change (1 = the largest decline).",
    ]
    for b in bullets:
        pdf.set_x(15)
        pdf.multi_cell(180, 5, f"- {b}")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(15)
    pdf.cell(0, 7, "How to read this", ln=1)
    pdf.set_font("Helvetica", size=10)
    pdf.set_x(15)
    pdf.multi_cell(180, 5, "These figures come from CMS's public monthly Performance Indicator enrollment file on data.medicaid.gov. For each state and month, an Updated report was used when available; otherwise the Preliminary report was used. National totals are the sum of states that reported a total for that month, not a separate CMS national line. Enrollment can fall because people were found ineligible, moved to other coverage, or were disenrolled for procedural reasons, and it can also change because of births, new applications, or data revisions.")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(15)
    pdf.cell(0, 7, "Important limits", ln=1)
    pdf.set_font("Helvetica", size=10)
    pdf.set_x(15)
    pdf.multi_cell(180, 5, "This is not a caseload forecast and not an official CMS or Colorado Department of Health Care Policy and Financing brief. Footnotes in the source file can affect comparability (for example, when a state includes or excludes a population). The latest month in this extract, July 2026, is Preliminary for all 51 states (50 states and the District of Columbia). Missing months are not imputed. The analysis does not identify why any individual lost or gained coverage, and it does not use personal health information.")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(15)
    pdf.cell(0, 7, "Source and contact path for more detail", ln=1)
    pdf.set_font("Helvetica", size=10)
    pdf.set_x(15)
    pdf.multi_cell(180, 5, "CMS, State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data, data.medicaid.gov. Full methods, data-quality checks, charts, and an interactive dashboard are in the project README.")

    out = OUT / "stakeholder_summary.pdf"
    pdf.output(str(out))
    print(f"Wrote {out}")

    md = ROOT / "STAKEHOLDER_SUMMARY.md"
    md.write_text(
        "\n".join([
            "# Medicaid and CHIP Enrollment During the Unwinding Period",
            "",
            "A one-page briefing for nontechnical stakeholders. Colorado focus, with a national comparison.",
            "",
            "## The question",
            "",
            "After the COVID-19 continuous coverage requirement ended on March 31, 2023, states resumed eligibility renewals (the \"unwinding\"). How did Medicaid and CHIP enrollment change in Colorado and across states from March 2023 through the latest public CMS monthly report?",
            "",
            "## What the public data show",
            "",
            f"- In March 2023, Colorado reported {fmt(co_base['total_enrollment'])} people enrolled in Medicaid and CHIP. By {last_label}, that figure was {fmt(co_last['total_enrollment'])}, a change of {fmt(co_last['change_count'])} people, or {co_pct:.1f}%.",
            f"- Across states with usable data, combined enrollment went from {fmt(nat_base['total_enrollment'])} in March 2023 ({int(nat_base['states_with_total_enrollment'])} states) to {fmt(nat_last['total_enrollment'])} in {last_label} ({int(nat_last['states_with_total_enrollment'])} states), a change of {nat_pct:.1f}%.",
            f"- Among {n_states} states with both a March 2023 baseline and a {last_label} total, Colorado ranked {co_rank} in percent change (1 = the largest decline).",
            "",
            "## How to read this",
            "",
            "These figures come from CMS's public monthly Performance Indicator enrollment file on data.medicaid.gov. For each state and month, an Updated report was used when available; otherwise the Preliminary report was used. National totals are the sum of states that reported a total for that month, not a separate CMS national line.",
            "",
            "## Important limits",
            "",
            "This is not a caseload forecast and not an official CMS or state brief. Footnotes can affect comparability. The latest month in this extract, July 2026, is Preliminary for all 51 states (50 states and the District of Columbia). Missing months are not imputed. The analysis does not identify why any individual lost or gained coverage and does not use personal health information.",
            "",
            "## Source",
            "",
            "CMS, State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data, https://data.medicaid.gov/dataset/6165f45b-ca93-5bb5-9d06-db29c692a360/",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"Wrote {md}")


def main() -> None:
    co = pd.read_csv(TABLES / "measure_colorado_vs_baseline.csv")
    nat = pd.read_csv(TABLES / "measure_national_vs_baseline.csv")
    chg = pd.read_csv(TABLES / "measure_state_change_to_latest.csv")
    build_dashboard(co, nat, chg)
    build_pdf(co, nat, chg)


if __name__ == "__main__":
    main()
