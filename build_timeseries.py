"""
Build tidy, analysis-ready CSVs from the daily crime report JSON files.

Outputs (all under data/):
  daily_counts.csv   - one row per (date, offense): the canonical daily count.
                       Each daily report restates the trailing 7 days, so the
                       same (date, offense) appears in up to 7 reports; the
                       most recent report wins.
  report_metrics.csv - one row per (report_date, offense): 7-day totals, YTD
                       totals, and changes. Weekly/YTD changes are recomputed
                       from the raw counts because files written before the
                       parser fix stored the YTD change under both keys.
  revisions.csv      - every case where a report restated a previously
                       published daily count with a different value. These are
                       silent reclassifications by PGPD and story leads in
                       their own right.

Stdlib only, so it runs anywhere without installing dependencies.

Usage: python3 build_timeseries.py
"""

import csv
import json
import re
from pathlib import Path

from crime_categories import categorize, clean_records

DATA_DIR = Path(__file__).parent / "data"
JSON_DIR = DATA_DIR / "json"

DATE_KEY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_reports():
    """Load all daily JSON files, oldest first, with cleaned records."""
    reports = []
    for path in sorted(JSON_DIR.glob("*.json")):
        if path.name == "manifest.json":
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        report_date = data.get("report_date")
        if not report_date:
            continue
        records = clean_records(data.get("crime_statistics", []))
        reports.append({"report_date": report_date, "records": records})
    reports.sort(key=lambda r: r["report_date"])
    return reports


def daily_counts_from_record(record):
    """Extract {iso_date: count} from a report row's dynamic date keys."""
    return {
        key: value
        for key, value in record.items()
        if DATE_KEY_RE.match(key) and isinstance(value, int)
    }


def pct_change(current, previous):
    """Percent change, blank when the base is zero (a 0 -> N jump has no
    meaningful percentage and shouldn't be quoted as one)."""
    if previous == 0:
        return ""
    return round((current - previous) / previous * 100, 1)


def build(reports):
    # canonical[(offense, date)] = (count, source_report)
    canonical = {}
    revisions = []
    metrics_rows = []

    for report in reports:
        report_date = report["report_date"]
        for record in report["records"]:
            offense = record["offense_type"]

            for date, count in daily_counts_from_record(record).items():
                key = (offense, date)
                if key in canonical and canonical[key][0] != count:
                    prev_count, prev_report = canonical[key]
                    revisions.append({
                        "offense_type": offense,
                        "date": date,
                        "previous_count": prev_count,
                        "revised_count": count,
                        "previous_report": prev_report,
                        "revised_report": report_date,
                    })
                canonical[key] = (count, report_date)

            seven = record.get("seven_day_total")
            prev_seven = record.get("prev_seven_day_total")
            ytd_2026 = record.get("ytd_2026")
            ytd_2025 = record.get("ytd_2025")
            if not all(isinstance(v, int) for v in (seven, prev_seven, ytd_2026, ytd_2025)):
                continue

            metrics_rows.append({
                "report_date": report_date,
                "offense_type": offense,
                "category": categorize(offense),
                "seven_day_total": seven,
                "prev_seven_day_total": prev_seven,
                "weekly_change": seven - prev_seven,
                "weekly_percent_change": pct_change(seven, prev_seven),
                "ytd_2026": ytd_2026,
                "ytd_2025": ytd_2025,
                "ytd_change": ytd_2026 - ytd_2025,
                "ytd_percent_change": pct_change(ytd_2026, ytd_2025),
            })

    daily_rows = [
        {
            "date": date,
            "offense_type": offense,
            "category": categorize(offense),
            "count": count,
            "source_report": source,
        }
        for (offense, date), (count, source) in sorted(
            canonical.items(), key=lambda item: (item[0][1], item[0][0])
        )
    ]

    return daily_rows, metrics_rows, revisions


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def main():
    reports = load_reports()
    print(f"Loaded {len(reports)} daily reports "
          f"({reports[0]['report_date']} to {reports[-1]['report_date']})")

    daily_rows, metrics_rows, revisions = build(reports)

    write_csv(DATA_DIR / "daily_counts.csv", daily_rows,
              ["date", "offense_type", "category", "count", "source_report"])
    write_csv(DATA_DIR / "report_metrics.csv", metrics_rows,
              ["report_date", "offense_type", "category",
               "seven_day_total", "prev_seven_day_total",
               "weekly_change", "weekly_percent_change",
               "ytd_2026", "ytd_2025", "ytd_change", "ytd_percent_change"])
    write_csv(DATA_DIR / "revisions.csv", revisions,
              ["offense_type", "date", "previous_count", "revised_count",
               "previous_report", "revised_report"])


if __name__ == "__main__":
    main()
