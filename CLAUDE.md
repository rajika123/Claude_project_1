# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) when working with this repository.

## Repository Overview

This repository contains a **Cab Price Monitor** — a Python tool that continuously tracks Uber and Ola prices for a fixed route, analyses surge patterns, and emails a recommendation every 3 hours suggesting the best time to take a cab.

**Remote**: `http://local_proxy@127.0.0.1:40229/git/rajika123/Claude_project_1`

---

## Project Structure

```
cab_price_monitor/
├── main.py         # Entry point & scheduler
├── config.py       # Route, email, and fare configuration (edit this first)
├── fetcher.py      # Price fetching (simulated Uber/Ola with surge model)
├── analyzer.py     # Price history, trend analysis, and recommendation engine
├── notifier.py     # HTML + plain-text email builder and sender
└── requirements.txt
```

---

## Quick Start

```bash
cd cab_price_monitor
pip install -r requirements.txt

# Try the demo (no email sent, simulates 3 hours of data)
python main.py --demo

# Run the live monitor (sends emails)
python main.py
```

---

## Configuration

Edit `cab_price_monitor/config.py` before running:

| Setting             | Description                                      |
|---------------------|--------------------------------------------------|
| `ORIGIN`            | Pickup location (text label)                     |
| `DESTINATION`       | Drop-off location (text label)                   |
| `ROUTE_DISTANCE_KM` | Approximate route distance for fare calculation  |
| `ROUTE_BASE_TIME_MIN` | Baseline travel time in minutes               |
| `FETCH_INTERVAL_MIN`| How often prices are sampled (default: 5 min)    |
| `REPORT_INTERVAL_HR`| How often email reports are sent (default: 3 hr) |
| `EMAIL_SENDER`      | Gmail address to send from                       |
| `EMAIL_PASSWORD`    | Gmail App Password (not your main password)      |
| `EMAIL_RECEIVER`    | Address to receive reports                       |
| `SERVICES`          | Base fares per km/min for each ride type         |

### Gmail App Password setup
1. Enable 2-Step Verification on your Google account
2. Go to Google Account → Security → App Passwords
3. Generate a password for "Mail" and paste it as `EMAIL_PASSWORD`

---

## Architecture

### Data Flow

```
schedule (every 5 min)
    └─▶ fetcher.fetch_all_prices()
            └─▶ PriceQuote list (sorted by total_fare)
                    └─▶ PriceHistory.record()

schedule (every 3 hr)
    └─▶ analyzer.build_recommendation(history, current_quotes)
            └─▶ Recommendation
                    └─▶ notifier.send_report()  →  email
                    └─▶ console print
```

### Surge Model (`fetcher.py`)

Because Uber and Ola do not offer public price APIs, the fetcher uses a realistic simulation:

- **Peak windows**: morning rush (07:00–09:30), lunch (12:00–13:30), evening rush (17:30–20:00), late-night (22:00–24:00)
- **Surge**: Gaussian bell curve centred at each peak, capped at 1.0× minimum
- **Travel time**: increases proportionally with surge (more traffic = longer journey)
- **ETA**: more drivers are available off-peak

To use a real API, replace `_fetch_uber()` / `_fetch_ola()` in `fetcher.py` with actual HTTP calls — the return type (`dict[str, PriceQuote]`) stays the same.

### Recommendation logic (`analyzer.py`)

| Scenario             | Advice                                |
|----------------------|---------------------------------------|
| Current ≤ 3h-low ×1.05 | "Book now — near the 3-hour low" |
| Trend falling        | "Wait 10–20 minutes"                  |
| Trend rising         | "Book now before prices rise further" |
| Stable               | Show best option and 3h low           |

Trend is computed via linear regression slope on the fare time series.

---

## Development Conventions

### Adding a new cab service

1. Add an entry to `config.SERVICES` with base fares.
2. Add a `_fetch_<service>(hour)` function in `fetcher.py` following the same pattern.
3. Call it from `fetch_all_prices()` and extend the returned list.

### Changing the notification channel

Replace `notifier.send_report()` with your preferred channel (SMS, Slack, etc.). The `Recommendation` object passed to it contains all the data you need.

### Testing the surge model

Run the demo with a custom hour by temporarily changing the `base` time in `main.run_demo()`:
```python
base = datetime.now().replace(hour=18, minute=0, second=0)  # simulate 6 PM rush
```

---

## Git Configuration

- **Commit signing**: SSH signing enabled (`commit.gpgsign=true`)
- **Signing key**: `/home/claude/.ssh/commit_signing_key.pub`

### Branch strategy
- Feature branches: `claude/<description>-<session-id>`
- Always push with: `git push -u origin <branch-name>`

### Push retry (network errors only)
Backoff: 2s → 4s → 8s → 16s. Do **not** retry on HTTP 403.

---

## AI Assistant Guidelines

- **Read before editing**: Always read a file before modifying it.
- **Minimal changes**: Only change what is necessary for the task.
- **No invented URLs**: Do not generate or guess URLs unless confident.
- **Security-first**: Never commit `EMAIL_PASSWORD` or other credentials.
- **Branch discipline**: Always work on the designated feature branch.

---

## Updating This File

Update CLAUDE.md when:
- New cab services are added
- The notification channel changes
- Real API credentials/calls are integrated
- New configuration options are added
