#!/usr/bin/env python3
"""Run SQL performance measures in SQLite and export CSV tables."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean" / "enrollment_preferred_series.csv"
SQL_FILE = ROOT / "sql" / "enrollment_measures.sql"
OUT = ROOT / "output"
DB = OUT / "enrollment_measures.sqlite"
TABLE_DIR = OUT / "tables"
OUT.mkdir(exist_ok=True)
TABLE_DIR.mkdir(exist_ok=True)


def main() -> None:
    df = pd.read_csv(CLEAN, parse_dates=["period"])
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    df.to_sql("enrollment", conn, index=False, if_exists="replace")
    sql = SQL_FILE.read_text(encoding="utf-8")
    conn.executescript(sql)
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'measure_%' ORDER BY name"
        )
    ]
    for name in tables:
        t = pd.read_sql(f'SELECT * FROM "{name}"', conn)
        t.to_csv(TABLE_DIR / f"{name}.csv", index=False)
        print(f"{name}: {len(t):,} rows")
    conn.close()
    print(f"SQLite database: {DB}")


if __name__ == "__main__":
    main()
