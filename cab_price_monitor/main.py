"""
Cab Price Monitor — entry point.

Usage:
    python main.py              # run the live monitor
    python main.py --demo       # print one report to stdout without emailing

Scheduler:
  - Every FETCH_INTERVAL_MIN  : fetch prices and record to history
  - Every REPORT_INTERVAL_HR  : analyse history, print summary, send email
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

import schedule

import config
from analyzer import PriceHistory, build_recommendation
from fetcher import fetch_all_prices
from notifier import build_plain, send_report


# ── Shared state ──────────────────────────────────────────────────────────────

history = PriceHistory()


# ── Jobs ──────────────────────────────────────────────────────────────────────

def job_fetch() -> None:
    """Fetch current prices and add them to history. Runs every FETCH_INTERVAL_MIN."""
    now    = datetime.now()
    quotes = fetch_all_prices(at=now)
    history.record(quotes, at=now)

    best = quotes[0]
    print(
        f"[{now.strftime('%H:%M:%S')}] "
        f"Fetched {len(quotes)} quotes | "
        f"Best: {best.service} {best.ride_type} ₹{best.total_fare:.0f} "
        f"(surge ×{best.surge_multiplier:.2f})"
    )


def job_report(send_email: bool = True) -> None:
    """Build and (optionally) email the 3-hour recommendation. Runs every REPORT_INTERVAL_HR."""
    if history.count == 0:
        print("No history yet — skipping report.")
        return

    current_quotes = fetch_all_prices()
    history.record(current_quotes)

    rec = build_recommendation(history, current_quotes)

    # Always print to console
    print("\n" + "=" * 60)
    print(build_plain(rec, current_quotes))
    print("=" * 60 + "\n")

    if send_email:
        try:
            send_report(rec, current_quotes)
        except Exception as exc:
            print(f"[WARNING] Email failed: {exc}", file=sys.stderr)
            print("Check EMAIL_SENDER / EMAIL_PASSWORD / EMAIL_RECEIVER in config.py")


# ── Demo mode ─────────────────────────────────────────────────────────────────

def run_demo() -> None:
    """
    Simulate 3 hours of data (one snapshot per FETCH_INTERVAL_MIN), then
    print the recommendation report without sending email.
    """
    from datetime import timedelta

    print("Running in DEMO mode — simulating 3 hours of price data...\n")
    base = datetime.now().replace(hour=8, minute=0, second=0)  # start at 08:00

    steps = int((config.REPORT_INTERVAL_HR * 60) / config.FETCH_INTERVAL_MIN)
    for i in range(steps + 1):
        t = base + timedelta(minutes=i * config.FETCH_INTERVAL_MIN)
        quotes = fetch_all_prices(at=t)
        history.record(quotes, at=t)

    current_quotes = fetch_all_prices()
    rec = build_recommendation(history, current_quotes)

    print(build_plain(rec, current_quotes))
    print(
        "\n[Demo] Email would be sent to:", config.EMAIL_RECEIVER,
        "\nSet send_email=True in run_demo() or use the live monitor to actually send emails."
    )


# ── Live monitor ──────────────────────────────────────────────────────────────

def run_live() -> None:
    print(f"Cab Price Monitor starting...")
    print(f"Route   : {config.ORIGIN} → {config.DESTINATION}")
    print(f"Fetch   : every {config.FETCH_INTERVAL_MIN} minutes")
    print(f"Reports : every {config.REPORT_INTERVAL_HR} hours  →  {config.EMAIL_RECEIVER}")
    print("Press Ctrl+C to stop.\n")

    # Run once immediately so we have data right away
    job_fetch()

    schedule.every(config.FETCH_INTERVAL_MIN).minutes.do(job_fetch)
    schedule.every(config.REPORT_INTERVAL_HR).hours.do(job_report, send_email=True)

    # Also send the first report after the first full fetch interval
    schedule.every(config.FETCH_INTERVAL_MIN).minutes.do(
        lambda: (schedule.cancel_job(schedule.jobs[-1]), job_report(send_email=True))
        if history.count >= 3 else None
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cab Price Monitor")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Simulate 3 hours of data and print a report without sending email.",
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_live()
