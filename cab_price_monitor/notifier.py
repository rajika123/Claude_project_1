"""
Email notifier — sends a formatted HTML + plain-text report every 3 hours.
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import config
from analyzer import Recommendation
from fetcher import PriceQuote


# ── Formatting helpers ────────────────────────────────────────────────────────

def _surge_colour(multiplier: float) -> str:
    if multiplier < 1.3:
        return "#27ae60"   # green
    if multiplier < 1.6:
        return "#f39c12"   # orange
    return "#e74c3c"       # red


def _trend_icon(trend: str) -> str:
    return {"rising": "📈", "falling": "📉", "stable": "➡️"}.get(trend, "")


def _quote_rows_html(quotes: list[PriceQuote]) -> str:
    rows = []
    for i, q in enumerate(quotes):
        bg = "#eafaf1" if i == 0 else "#ffffff"
        best_tag = " ⭐ Best" if i == 0 else ""
        rows.append(
            f"<tr style='background:{bg}'>"
            f"<td>{q.service}</td>"
            f"<td>{q.ride_type}</td>"
            f"<td><b>₹{q.total_fare:.0f}</b></td>"
            f"<td style='color:{_surge_colour(q.surge_multiplier)}'>"
            f"×{q.surge_multiplier:.2f} ({q.surge_label})</td>"
            f"<td>{q.eta_minutes} min</td>"
            f"<td>{q.travel_time_minutes} min</td>"
            f"<td>{best_tag}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _avg_rows_html(avg_fare_by_key: dict[str, float]) -> str:
    sorted_avgs = sorted(avg_fare_by_key.items(), key=lambda x: x[1])
    rows = []
    for key, avg in sorted_avgs:
        rows.append(
            f"<tr><td>{key}</td><td>₹{avg:.0f}</td></tr>"
        )
    return "\n".join(rows)


def build_html(rec: Recommendation, current_quotes: list[PriceQuote]) -> str:
    trend_icon = _trend_icon(rec.trend)
    good_time_banner = (
        '<div style="background:#d5f5e3;padding:12px;border-radius:6px;margin-bottom:16px">'
        '✅ <b>Good time to book!</b> Current prices are near the 3-hour low.'
        '</div>'
    ) if rec.is_good_time else (
        '<div style="background:#fef9e7;padding:12px;border-radius:6px;margin-bottom:16px">'
        '⏳ You may save money by waiting. See recommendation below.'
        '</div>'
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; color: #333; max-width: 700px; margin: auto; padding: 20px; }}
    h1   {{ color: #2c3e50; }}
    h2   {{ color: #2980b9; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
    th, td {{ text-align: left; padding: 8px 12px; border: 1px solid #ddd; }}
    th {{ background: #2980b9; color: white; }}
    .advice {{ background:#eaf2ff; padding:14px; border-radius:6px; font-size:15px; line-height:1.6; }}
    .footer {{ color:#999; font-size:12px; margin-top:30px; }}
  </style>
</head>
<body>
  <h1>🚕 Cab Price Report — 3-Hour Summary</h1>
  <p><b>Route:</b> {config.ORIGIN} → {config.DESTINATION}</p>
  <p><b>Generated:</b> {rec.generated_at.strftime('%A, %d %b %Y at %H:%M')}</p>

  {good_time_banner}

  <h2>💡 Recommendation</h2>
  <div class="advice">{rec.advice}</div>

  <h2>📊 Current Prices {trend_icon} (trend: {rec.trend})</h2>
  <table>
    <tr>
      <th>Service</th><th>Ride Type</th><th>Fare</th>
      <th>Surge</th><th>ETA</th><th>Travel Time</th><th></th>
    </tr>
    {_quote_rows_html(current_quotes)}
  </table>

  <h2>📉 3-Hour Average Fares</h2>
  <table>
    <tr><th>Service & Ride Type</th><th>Avg Fare</th></tr>
    {_avg_rows_html(rec.avg_fare_by_key)}
  </table>

  <h2>🏆 3-Hour Best Price</h2>
  <p>
    <b>{rec.window_best.service} {rec.window_best.ride_type}</b>
    at <b>₹{rec.window_best.total_fare:.0f}</b>
    (surge ×{rec.window_best.surge_multiplier:.2f})
    seen at <b>{rec.window_best_time.strftime('%H:%M')}</b>.
  </p>

  <p class="footer">
    Prices are updated every {config.FETCH_INTERVAL_MIN} minutes.
    This report is sent every {config.REPORT_INTERVAL_HR} hours.<br>
    Powered by Cab Price Monitor.
  </p>
</body>
</html>
""".strip()


def build_plain(rec: Recommendation, current_quotes: list[PriceQuote]) -> str:
    lines = [
        "=== Cab Price Report (3-Hour Summary) ===",
        f"Route : {config.ORIGIN} → {config.DESTINATION}",
        f"Time  : {rec.generated_at.strftime('%A, %d %b %Y at %H:%M')}",
        "",
        f"RECOMMENDATION ({rec.trend} trend):",
        rec.advice,
        "",
        "CURRENT PRICES:",
    ]
    for i, q in enumerate(current_quotes):
        tag = " [BEST]" if i == 0 else ""
        lines.append(
            f"  {q.service:6} {q.ride_type:15} ₹{q.total_fare:>6.0f}  "
            f"surge×{q.surge_multiplier:.2f} ({q.surge_label:15})  "
            f"ETA {q.eta_minutes}min  travel ~{q.travel_time_minutes}min{tag}"
        )
    lines += [
        "",
        "3-HOUR AVERAGES:",
    ]
    for key, avg in sorted(rec.avg_fare_by_key.items(), key=lambda x: x[1]):
        lines.append(f"  {key:25} avg ₹{avg:.0f}")
    lines += [
        "",
        f"3-HOUR BEST: {rec.window_best.service} {rec.window_best.ride_type} "
        f"₹{rec.window_best.total_fare:.0f} at {rec.window_best_time.strftime('%H:%M')}",
    ]
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def send_report(rec: Recommendation, current_quotes: list[PriceQuote]) -> None:
    """Send the 3-hour recommendation email."""
    subject = (
        f"[Cab Monitor] {'✅ Book Now' if rec.is_good_time else '⏳ Wait for better price'} "
        f"— Best: ₹{rec.best_now.total_fare:.0f} ({rec.best_now.service} {rec.best_now.ride_type})"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = config.EMAIL_SENDER
    msg["To"]      = config.EMAIL_RECEIVER

    msg.attach(MIMEText(build_plain(rec, current_quotes), "plain"))
    msg.attach(MIMEText(build_html(rec, current_quotes),  "html"))

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
        server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECEIVER, msg.as_string())

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Email report sent to {config.EMAIL_RECEIVER}")
