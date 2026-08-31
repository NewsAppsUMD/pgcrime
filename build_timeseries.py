#!/usr/bin/env python3
"""
Build timeseries.json from the archive of daily crime report JSON files.

Each daily report contains a rolling 7-day window plus year-to-date totals.
This script walks the archive and produces a compact per-offense time series
so the dashboard can render historical trend charts.
"""

import json
from pathlib import Path

SERIES_KEYS = ('seven_day_total', 'prev_seven_day_total', 'ytd_2026', 'ytd_2025')


def build_timeseries():
    data_dir = Path(__file__).parent / 'data' / 'json'

    report_files = sorted(
        f for f in data_dir.glob('*.json')
        if f.name not in ('manifest.json', 'timeseries.json')
    )

    dates = []
    offenses = {}

    for path in report_files:
        try:
            report = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skipping {path.name}: {e}")
            continue

        report_date = report.get('report_date')
        if not report_date:
            print(f"Skipping {path.name}: no report_date")
            continue

        dates.append(report_date)

        # Some reports list an offense type twice; keep the first occurrence.
        seen = set()
        for stat in report.get('crime_statistics', []):
            name = stat.get('offense_type')
            if not name or name in seen:
                continue
            seen.add(name)
            series = offenses.setdefault(name, {key: [] for key in SERIES_KEYS})
            for key in SERIES_KEYS:
                series[key].append(stat.get(key))

        # Keep every series aligned with the dates array.
        for series in offenses.values():
            for key in SERIES_KEYS:
                while len(series[key]) < len(dates):
                    series[key].append(None)

    timeseries = {'dates': dates, 'offenses': offenses}

    out_path = data_dir / 'timeseries.json'
    with open(out_path, 'w') as f:
        json.dump(timeseries, f)

    print(f"✓ Wrote {out_path}")
    print(f"  Dates: {len(dates)} ({dates[0] if dates else '-'} → {dates[-1] if dates else '-'})")
    print(f"  Offenses: {len(offenses)}")


if __name__ == '__main__':
    build_timeseries()
