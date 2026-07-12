"""
Alert engine + morning briefing for the PG County crime data pipeline.

Deterministically replays the full report history on every run, computing
alerts for each report date using only data that was available on that date.
New alerts (ids not present in the existing log) are the ones worth
notifying about; everything else is a no-op rewrite, so the script is
idempotent and safe to re-run.

Alert types:
  spike / dip      7-day total significantly above/below its recent baseline
  record_high      highest 7-day total since tracking began
  milestone        YTD count crossed a round-number threshold
  pace_flip        YTD count crossed last year's pace (in either direction)
  streak           longest stretch without a headline offense on record
  revision         a previously published daily count was quietly changed

Outputs:
  data/alerts/alerts.json   full alert log (committed, the system of record)
  docs/data/alerts.json     latest alerts for the website
  docs/data/briefing.json   morning-memo content for the website
  docs/alerts.xml           RSS feed of alerts
  --issue-out PREFIX        writes PREFIX-title.txt / PREFIX-body.md for
                            `gh issue create` when new alerts fired
  $GITHUB_OUTPUT            new_alert_count=<n> when running in Actions

If SLACK_WEBHOOK_URL is set, posts the briefing (with any new alerts) to
Slack whenever the latest report produced new alerts or --slack-daily is
passed. Stdlib only.

Usage: python3 generate_alerts.py [--issue-out PREFIX] [--no-slack] [--slack-daily]
"""

import argparse
import json
import os
import re
import statistics
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from build_timeseries import daily_counts_from_record, load_reports
from crime_categories import HEADLINE_OFFENSES, SUBTYPE_OFFENSES, TOTAL_ROWS

BASE_DIR = Path(__file__).parent
ALERTS_DIR = BASE_DIR / "data" / "alerts"
DOCS_DATA_DIR = BASE_DIR / "docs" / "data"
SITE_URL = "https://newsappsumd.github.io/pgcrime/"
TRACKING_START_NOTE = "since tracking began Feb. 8, 2026"

# --- Tunables (calibrated by replaying the Feb-Jul 2026 history) ---
SPIKE_Z = 2.0                 # std deviations above baseline mean
SPIKE_MIN_COUNT = 5           # ignore spikes in very low-volume offenses
DIP_MIN_MEAN = 8              # only flag dips for offenses with real volume
BASELINE_WEEKS = 8            # how many trailing weekly samples to use
BASELINE_MIN_SAMPLES = 4
RECORD_MIN_HISTORY_DAYS = 56  # don't call records until 8 weeks of data
COOLDOWN_DAYS = 6             # overlapping 7-day windows re-trigger; damp them
STREAK_MIN_DAYS = 10
PACE_MIN_YTD = 20             # both years need volume before pace flips matter
PACE_MIN_MARGIN = 5           # and the flip must be decisive, not jitter
# Round-number milestones only matter for the offenses reporters track
MILESTONE_OFFENSES = set(HEADLINE_OFFENSES) | set(TOTAL_ROWS)
REVISION_MIN_AGE_DAYS = 4     # older-than-this revisions are reclassifications,
                              # not routine trickle-in of late reports
SERIOUS_REVISION_OFFENSES = {"Murder", "Non-Fatal Shooting", "Carjacking", "Rape"}

CAVEATS = [
    "Figures cover crimes reported within PGPD's primary jurisdiction; "
    "municipal police departments (Laurel, Bowie, Greenbelt, Hyattsville and "
    "others) are not included.",
    "Data is subject to change as incidents are investigated and reclassified.",
    "PGPD's categories differ from FBI UCR definitions.",
]


def fmt_date(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%b. %-d, %Y")


def fmt_date_short(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%b. %-d")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def pct_text(current, previous):
    if previous == 0:
        return None
    pct = (current - previous) / previous * 100
    direction = "up" if pct > 0 else "down"
    return f"{direction} {abs(pct):.0f}%"


def offense_severity(offense):
    """Headline offenses are high priority, granular subtypes are
    informational, everything else (parent categories, totals) is medium."""
    if offense in HEADLINE_OFFENSES:
        return "high"
    if offense in SUBTYPE_OFFENSES:
        return "info"
    return "medium"


def milestone_step(ytd):
    if ytd < 300:
        return 25
    if ytd < 1500:
        return 100
    if ytd < 6000:
        return 500
    return 1000


class AlertEngine:
    def __init__(self, reports):
        self.reports = reports
        self.alerts = []
        # State accumulated as the replay walks forward in time
        self.canonical = {}            # (offense, date) -> count as of "now"
        self.history = {}              # offense -> [(report_date, metrics), ...]
        self.record_high = {}          # offense -> best 7-day total seen
        self.streak_record = {}        # offense -> longest zero-streak seen
        self.last_fired = {}           # (type, offense) -> report_date

    def run(self):
        for report in self.reports:
            self.process(report)
        return self.alerts

    # -- helpers ------------------------------------------------------------

    def add(self, report_date, kind, offense, severity, headline, detail):
        key = (kind, offense)
        last = self.last_fired.get(key)
        if last and (date.fromisoformat(report_date)
                     - date.fromisoformat(last)).days <= COOLDOWN_DAYS:
            return
        self.last_fired[key] = report_date
        self.alerts.append({
            "id": f"{report_date}-{kind}-{slug(offense)}",
            "report_date": report_date,
            "type": kind,
            "severity": severity,
            "offense_type": offense,
            "headline": headline,
            "detail": detail,
        })

    def baseline(self, offense, report_date):
        """Trailing weekly samples of the 7-day total, stepping back 7 days at
        a time and taking the nearest available report within 3 days."""
        entries = self.history.get(offense, [])
        if not entries:
            return []
        target = date.fromisoformat(report_date)
        samples = []
        for week in range(1, BASELINE_WEEKS + 1):
            want = target - timedelta(days=7 * week)
            best = None
            for entry_date, metrics in reversed(entries):
                delta = abs((date.fromisoformat(entry_date) - want).days)
                if delta <= 3 and (best is None or delta < best[0]):
                    best = (delta, metrics["seven_day_total"])
            if best:
                samples.append(best[1])
        return samples

    # -- per-report processing ----------------------------------------------

    def process(self, report):
        report_date = report["report_date"]
        prev_metrics = {off: entries[-1][1]
                        for off, entries in self.history.items() if entries}

        revisions = []
        for record in report["records"]:
            offense = record["offense_type"]
            metrics = {
                "seven_day_total": record.get("seven_day_total"),
                "prev_seven_day_total": record.get("prev_seven_day_total"),
                "ytd_2026": record.get("ytd_2026"),
                "ytd_2025": record.get("ytd_2025"),
            }
            if not all(isinstance(v, int) for v in metrics.values()):
                continue

            for day, count in daily_counts_from_record(record).items():
                key = (offense, day)
                if key in self.canonical and self.canonical[key] != count:
                    revisions.append((offense, day, self.canonical[key], count))
                self.canonical[key] = count

            self.check_spike_dip(report_date, offense, metrics)
            self.check_record(report_date, offense, metrics)
            self.check_milestone(report_date, offense, metrics,
                                 prev_metrics.get(offense))
            self.check_pace_flip(report_date, offense, metrics,
                                 prev_metrics.get(offense))

            self.history.setdefault(offense, []).append((report_date, metrics))

        self.check_streaks(report_date)
        self.check_revisions(report_date, revisions)

    def check_spike_dip(self, report_date, offense, metrics):
        samples = self.baseline(offense, report_date)
        if len(samples) < BASELINE_MIN_SAMPLES:
            return
        mean = statistics.mean(samples)
        stdev = statistics.stdev(samples)
        cur = metrics["seven_day_total"]
        window = f"the 7 days ending {fmt_date_short(report_date)}"

        if (cur >= SPIKE_MIN_COUNT and cur > max(samples)
                and stdev > 0 and cur > mean + SPIKE_Z * stdev):
            self.add(report_date, "spike", offense, offense_severity(offense),
                     f"{offense} spike: {cur} in the past 7 days",
                     f"{offense}: {cur} reported in {window}, vs. an average "
                     f"of {mean:.1f} per week over the prior "
                     f"{len(samples)} weeks — and above every one of those "
                     f"weeks. Worth a call to PGPD.")
        elif (mean >= DIP_MIN_MEAN and cur < min(samples)
                and stdev > 0 and cur < mean - SPIKE_Z * stdev):
            self.add(report_date, "dip", offense, "info",
                     f"{offense} at a recent low: {cur} in the past 7 days",
                     f"{offense}: {cur} reported in {window}, vs. an average "
                     f"of {mean:.1f} per week over the prior "
                     f"{len(samples)} weeks — below every one of those weeks.")

    def check_record(self, report_date, offense, metrics):
        cur = metrics["seven_day_total"]
        prev_record = self.record_high.get(offense)
        history = self.history.get(offense, [])
        enough_history = history and (
            date.fromisoformat(report_date)
            - date.fromisoformat(history[0][0])).days >= RECORD_MIN_HISTORY_DAYS

        if (enough_history and prev_record is not None
                and cur > prev_record and cur >= SPIKE_MIN_COUNT):
            self.add(report_date, "record_high", offense, offense_severity(offense),
                     f"{offense}: worst 7-day stretch on record ({cur})",
                     f"The {cur} {offense.lower()} reports in the 7 days "
                     f"ending {fmt_date_short(report_date)} are the most in "
                     f"any 7-day window {TRACKING_START_NOTE} "
                     f"(previous high: {prev_record}).")
        if prev_record is None or cur > prev_record:
            self.record_high[offense] = cur

    def check_milestone(self, report_date, offense, metrics, prev):
        if prev is None or offense not in MILESTONE_OFFENSES:
            return
        cur_ytd, prev_ytd = metrics["ytd_2026"], prev["ytd_2026"]
        step = milestone_step(cur_ytd)
        if cur_ytd // step > prev_ytd // step:
            crossed = (cur_ytd // step) * step
            severity = "high" if offense == "Murder" else "info"
            comparison = ""
            if metrics["ytd_2025"]:
                text = pct_text(cur_ytd, metrics["ytd_2025"])
                if text:
                    comparison = (f" That is {text} from this point in 2025 "
                                  f"({metrics['ytd_2025']}).")
            self.add(report_date, "milestone", offense, severity,
                     f"{offense}: {crossed} for the year",
                     f"{offense} reports reached {cur_ytd} for 2026 as of "
                     f"{fmt_date_short(report_date)}.{comparison}")

    def check_pace_flip(self, report_date, offense, metrics, prev):
        if prev is None:
            return
        if min(metrics["ytd_2026"], metrics["ytd_2025"]) < PACE_MIN_YTD:
            return
        cur_diff = metrics["ytd_2026"] - metrics["ytd_2025"]
        prev_diff = prev["ytd_2026"] - prev["ytd_2025"]
        if prev_diff == 0 or cur_diff == 0 or (cur_diff > 0) == (prev_diff > 0):
            return
        if abs(cur_diff) < PACE_MIN_MARGIN:
            return
        direction = "ahead of" if cur_diff > 0 else "behind"
        severity = "high" if offense in HEADLINE_OFFENSES + TOTAL_ROWS else "info"
        self.add(report_date, "pace_flip", offense, severity,
                 f"{offense} now {direction} last year's pace",
                 f"{offense}: {metrics['ytd_2026']} so far in 2026 vs. "
                 f"{metrics['ytd_2025']} at this point in 2025. Until this "
                 f"report, 2026 was {'behind' if cur_diff > 0 else 'ahead'}.")

    def current_streak(self, offense, as_of):
        """Consecutive days with zero reported incidents, ending at as_of."""
        streak = 0
        day = date.fromisoformat(as_of)
        while True:
            count = self.canonical.get((offense, day.isoformat()))
            if count is None or count > 0:
                break
            streak += 1
            day -= timedelta(days=1)
        return streak

    def check_streaks(self, report_date):
        for offense in HEADLINE_OFFENSES:
            streak = self.current_streak(offense, report_date)
            record = self.streak_record.get(offense, 0)
            if streak >= STREAK_MIN_DAYS and streak > record:
                self.add(report_date, "streak", offense, "medium",
                         f"{streak} days without a {offense.lower()} — "
                         f"longest stretch on record",
                         f"No {offense.lower()} reports since "
                         f"{fmt_date_short((date.fromisoformat(report_date) - timedelta(days=streak)).isoformat())}, "
                         f"the longest such stretch {TRACKING_START_NOTE}.")
            if streak > record:
                self.streak_record[offense] = streak

    def check_revisions(self, report_date, revisions):
        notable = []
        for offense, day, old, new in revisions:
            age = (date.fromisoformat(report_date) - date.fromisoformat(day)).days
            if offense == "Murder" or (offense in SERIOUS_REVISION_OFFENSES
                                       and age >= REVISION_MIN_AGE_DAYS):
                notable.append((offense, day, old, new))
        if not notable:
            return
        severity = "high" if any(o == "Murder" for o, *_ in notable) else "medium"
        lines = [f"{offense} on {fmt_date_short(day)}: {old} -> {new}"
                 for offense, day, old, new in notable]
        offenses = sorted({o for o, *_ in notable})
        self.add(report_date, "revision", ", ".join(offenses), severity,
                 f"PGPD revised previously published figures: {', '.join(offenses)}",
                 f"The {fmt_date_short(report_date)} report restates earlier "
                 f"daily counts: " + "; ".join(lines) + ". Reclassifications "
                 f"like these are worth asking the department about.")


# --- Morning briefing -------------------------------------------------------

def get_metric(records, offense):
    for record in records:
        if record["offense_type"] == offense:
            return record
    return None


def build_briefing(latest_report, todays_alerts, engine):
    report_date = latest_report["report_date"]
    records = latest_report["records"]
    memo = []

    total = get_metric(records, "Total Crime")
    if total:
        trend = pct_text(total["seven_day_total"], total["prev_seven_day_total"])
        memo.append(
            f"PGPD logged {total['seven_day_total']} crime reports in the 7 "
            f"days ending {fmt_date_short(report_date)}"
            + (f", {trend} from the week before" if trend else "")
            + f". Year to date: {total['ytd_2026']}, vs. {total['ytd_2025']} "
            f"at this point last year.")

    violent = get_metric(records, "Violent Crime Total")
    prop = get_metric(records, "Property Crime Total")
    if violent and prop:
        memo.append(
            f"The past week breaks down to {violent['seven_day_total']} "
            f"violent and {prop['seven_day_total']} property crime reports.")

    ytd_lines = []
    for offense in ("Murder", "Carjacking", "Non-Fatal Shooting"):
        record = get_metric(records, offense)
        if record:
            trend = pct_text(record["ytd_2026"], record["ytd_2025"])
            ytd_lines.append(
                f"{offense.lower()}s: {record['ytd_2026']} "
                f"({trend or 'even'} vs. 2025)")
    if ytd_lines:
        memo.append("Year to date — " + "; ".join(ytd_lines) + ".")

    murder_streak = engine.current_streak("Murder", report_date)
    if murder_streak >= 3:
        memo.append(f"No homicides reported in the past {murder_streak} days.")

    return {
        "report_date": report_date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "memo": memo,
        "alerts": todays_alerts,
        "caveats": CAVEATS,
    }


# --- Outputs ----------------------------------------------------------------

def write_rss(alerts, path):
    def esc(text):
        return (text.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;"))

    items = []
    for alert in alerts[:50]:
        pub = datetime.strptime(alert["report_date"], "%Y-%m-%d").replace(
            hour=14, tzinfo=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        items.append(
            "    <item>\n"
            f"      <title>{esc(alert['headline'])}</title>\n"
            f"      <description>{esc(alert['detail'])}</description>\n"
            f"      <link>{SITE_URL}</link>\n"
            f"      <guid isPermaLink=\"false\">{alert['id']}</guid>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f"      <category>{alert['type']}</category>\n"
            "    </item>")

    rss = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<rss version=\"2.0\">\n"
        "  <channel>\n"
        "    <title>Prince George's County Crime Alerts</title>\n"
        f"    <link>{SITE_URL}</link>\n"
        "    <description>Automated alerts from PGPD Daily Crime Report data: "
        "spikes, records, milestones, streaks and data revisions.</description>\n"
        + "\n".join(items) + "\n"
        "  </channel>\n"
        "</rss>\n")
    path.write_text(rss, encoding="utf-8")


def post_slack(briefing, new_alerts, webhook_url):
    lines = [f"*PG County crime briefing — {fmt_date(briefing['report_date'])}*", ""]
    lines += briefing["memo"]
    if new_alerts:
        lines += ["", "*Alerts:*"]
        emoji = {"high": ":rotating_light:", "medium": ":warning:", "info": ":information_source:"}
        for alert in new_alerts:
            lines.append(f"{emoji.get(alert['severity'], '')} *{alert['headline']}*")
            lines.append(f"    {alert['detail']}")
    lines += ["", f"<{SITE_URL}|Dashboard> · Not for publication without checking against the source PDF."]

    payload = json.dumps({"text": "\n".join(lines)}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        print(f"Posted briefing to Slack ({response.status})")


def write_issue_files(new_alerts, report_date, prefix):
    title = (new_alerts[0]["headline"] if len(new_alerts) == 1
             else f"Crime data alerts for {fmt_date(report_date)} ({len(new_alerts)})")
    body = [f"Automated alerts from the {fmt_date(report_date)} Daily Crime Report.", ""]
    for alert in new_alerts:
        body.append(f"### {alert['headline']}")
        body.append(f"**Type:** {alert['type']} · **Severity:** {alert['severity']}")
        body.append("")
        body.append(alert["detail"])
        body.append("")
    body.append(f"[Dashboard]({SITE_URL})")
    Path(f"{prefix}-title.txt").write_text(title, encoding="utf-8")
    Path(f"{prefix}-body.md").write_text("\n".join(body), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-out", help="path prefix for GitHub issue title/body files")
    parser.add_argument("--no-slack", action="store_true", help="never post to Slack")
    parser.add_argument("--slack-daily", action="store_true",
                        help="post the briefing to Slack even with no new alerts")
    args = parser.parse_args()

    reports = load_reports()
    if not reports:
        print("No reports found; nothing to do.")
        return

    engine = AlertEngine(reports)
    alerts = engine.run()

    log_path = ALERTS_DIR / "alerts.json"
    known_ids = set()
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            known_ids = {a["id"] for a in json.load(f)}
    new_alerts = [a for a in alerts if a["id"] not in known_ids]

    latest = reports[-1]
    todays_alerts = [a for a in alerts if a["report_date"] == latest["report_date"]]
    briefing = build_briefing(latest, todays_alerts, engine)

    newest_first = list(reversed(alerts))
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2, ensure_ascii=False)
    with open(DOCS_DATA_DIR / "alerts.json", "w", encoding="utf-8") as f:
        json.dump(newest_first[:50], f, indent=2, ensure_ascii=False)
    with open(DOCS_DATA_DIR / "briefing.json", "w", encoding="utf-8") as f:
        json.dump(briefing, f, indent=2, ensure_ascii=False)
    write_rss(newest_first, BASE_DIR / "docs" / "alerts.xml")

    print(f"{len(alerts)} alerts total, {len(new_alerts)} new "
          f"(latest report {latest['report_date']})")
    for alert in new_alerts:
        print(f"  [{alert['severity']}] {alert['headline']}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"new_alert_count={len(new_alerts)}\n")

    if new_alerts and args.issue_out:
        write_issue_files(new_alerts, latest["report_date"], args.issue_out)

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook_url and not args.no_slack and (new_alerts or args.slack_daily):
        try:
            post_slack(briefing, new_alerts, webhook_url)
        except Exception as e:  # notification failure shouldn't fail the run
            print(f"Slack post failed: {e}")


if __name__ == "__main__":
    main()
