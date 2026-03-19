"""
Price history store and recommendation engine.

The analyzer keeps an in-memory rolling window of PriceQuote snapshots and
answers two questions every time it is asked:

1. Right now — which service/ride-type is cheapest?
2. Looking at the last REPORT_INTERVAL_HR hours of data — when was the best
   time to travel, and is now a good time compared to that baseline?
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import NamedTuple

import config
from fetcher import PriceQuote


# ── History store ─────────────────────────────────────────────────────────────

class Snapshot(NamedTuple):
    timestamp: datetime
    quotes: list[PriceQuote]


class PriceHistory:
    """Rolling window of price snapshots, kept for REPORT_INTERVAL_HR hours."""

    def __init__(self) -> None:
        self._snapshots: list[Snapshot] = []

    def record(self, quotes: list[PriceQuote], at: datetime | None = None) -> None:
        self._snapshots.append(Snapshot(at or datetime.now(), quotes))
        self._evict()

    def _evict(self) -> None:
        cutoff = datetime.now() - timedelta(hours=config.REPORT_INTERVAL_HR)
        self._snapshots = [s for s in self._snapshots if s.timestamp >= cutoff]

    @property
    def snapshots(self) -> list[Snapshot]:
        return list(self._snapshots)

    @property
    def count(self) -> int:
        return len(self._snapshots)


# ── Recommendation ─────────────────────────────────────────────────────────────

@dataclass
class Recommendation:
    best_now: PriceQuote                     # cheapest quote right now
    window_best: PriceQuote                  # cheapest quote seen in the window
    window_best_time: datetime               # when that best quote occurred
    avg_fare_by_key: dict[str, float]        # "Service RideType" → average fare
    trend: str                               # "rising", "falling", "stable"
    advice: str                              # human-readable suggestion
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def is_good_time(self) -> bool:
        """True if current best fare is within 10% of the window's best fare."""
        return self.best_now.total_fare <= self.window_best.total_fare * 1.10


def _trend(fares: list[float]) -> str:
    """Return 'rising', 'falling', or 'stable' based on simple linear slope."""
    if len(fares) < 3:
        return "stable"
    n = len(fares)
    xs = list(range(n))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(fares)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, fares)) / \
            sum((x - x_mean) ** 2 for x in xs)
    pct_change = slope * n / y_mean if y_mean else 0
    if pct_change > 0.05:
        return "rising"
    if pct_change < -0.05:
        return "falling"
    return "stable"


def _key(q: PriceQuote) -> str:
    return f"{q.service} {q.ride_type}"


def build_recommendation(history: PriceHistory, current_quotes: list[PriceQuote]) -> Recommendation:
    """
    Analyse the price history and current snapshot to produce a recommendation.
    """
    best_now = current_quotes[0]   # list is pre-sorted by total_fare

    # Aggregate fares across all snapshots per service+ride-type key
    fare_series: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    for snap in history.snapshots:
        for q in snap.quotes:
            fare_series[_key(q)].append((snap.timestamp, q.total_fare))

    # Find the global cheapest quote in the window
    window_best: PriceQuote | None = None
    window_best_time: datetime = datetime.now()
    for snap in history.snapshots:
        for q in snap.quotes:
            if window_best is None or q.total_fare < window_best.total_fare:
                window_best = q
                window_best_time = snap.timestamp

    if window_best is None:
        window_best = best_now
        window_best_time = datetime.now()

    # Average fare per key over the window
    avg_fare_by_key = {
        k: statistics.mean(f for _, f in series)
        for k, series in fare_series.items()
    }

    # Price trend for the cheapest category
    cheapest_key = _key(best_now)
    cheapest_series = [f for _, f in sorted(fare_series.get(cheapest_key, []))]
    trend = _trend(cheapest_series)

    # Build human advice
    savings = window_best.total_fare - best_now.total_fare
    wait_mins = int((window_best_time - datetime.now()).total_seconds() / 60) \
                if window_best_time > datetime.now() else 0

    if best_now.total_fare <= window_best.total_fare * 1.05:
        advice = (
            f"NOW is a great time to book! "
            f"{best_now.service} {best_now.ride_type} at ₹{best_now.total_fare:.0f} "
            f"is near the 3-hour low of ₹{window_best.total_fare:.0f}."
        )
    elif trend == "falling":
        advice = (
            f"Prices are falling. Consider waiting 10–20 minutes. "
            f"Best seen in the last 3h: ₹{window_best.total_fare:.0f} "
            f"({window_best.service} {window_best.ride_type} "
            f"at {window_best_time.strftime('%H:%M')})."
        )
    elif trend == "rising":
        advice = (
            f"Prices are rising — book now before it gets worse. "
            f"{best_now.service} {best_now.ride_type} at ₹{best_now.total_fare:.0f}."
        )
    else:
        advice = (
            f"Prices are stable. Best current option: "
            f"{best_now.service} {best_now.ride_type} at ₹{best_now.total_fare:.0f}. "
            f"The 3-hour low was ₹{window_best.total_fare:.0f} "
            f"({window_best.service} {window_best.ride_type})."
        )

    return Recommendation(
        best_now=best_now,
        window_best=window_best,
        window_best_time=window_best_time,
        avg_fare_by_key=avg_fare_by_key,
        trend=trend,
        advice=advice,
    )
