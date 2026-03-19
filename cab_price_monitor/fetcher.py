"""
Price fetcher for Uber and Ola.

Real APIs:
  - Uber: https://developer.uber.com/docs/riders/ride-requests/tutorials/api/python
  - Ola:  https://devportal.olacabs.com/ (requires partner approval)

Until you have API credentials, this module uses a realistic simulator that
models surge pricing based on time-of-day demand patterns.  To plug in a real
API simply replace the body of `_fetch_<service>` with your API call and keep
the return type the same (a dict of ride-type → PriceQuote).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime

import config


@dataclass
class PriceQuote:
    service: str
    ride_type: str
    base_fare: float          # INR, before surge
    surge_multiplier: float
    total_fare: float         # base_fare * surge_multiplier
    eta_minutes: int          # estimated pickup wait time
    travel_time_minutes: int  # estimated journey duration
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def surge_label(self) -> str:
        for (lo, hi), label in config.SURGE_LABELS.items():
            if lo <= self.surge_multiplier < hi:
                return label
        return "Unknown"

    def __str__(self) -> str:
        return (
            f"{self.service} {self.ride_type}: ₹{self.total_fare:.0f} "
            f"({self.surge_label} ×{self.surge_multiplier:.2f}) | "
            f"ETA {self.eta_minutes}min | Travel ~{self.travel_time_minutes}min"
        )


# ── Surge model ───────────────────────────────────────────────────────────────

def _surge_multiplier(hour: float, service: str) -> float:
    """
    Return a surge multiplier for the given hour of day (0–24).

    Peak windows (high demand):
      - 07:00–09:30  Morning rush
      - 12:00–13:30  Lunch
      - 17:30–20:00  Evening rush
      - 22:00–23:59  Late-night
    """
    peaks = [
        (7.0,  9.5,  1.9, 0.4),   # (start, end, centre_multiplier, std_dev)
        (12.0, 13.5, 1.4, 0.2),
        (17.5, 20.0, 2.1, 0.5),
        (22.0, 24.0, 1.6, 0.3),
    ]

    surge = 1.0
    for start, end, centre, std in peaks:
        if start <= hour <= end:
            # Gaussian bell centred in the peak window
            mid = (start + end) / 2
            surge = max(surge, centre * (1 - 0.3 * ((hour - mid) / (end - start)) ** 2))
            break

    # Add per-service and random jitter
    jitter = random.gauss(0, 0.05)
    service_bias = 0.05 if service == "Ola" else 0.0   # Ola slightly cheaper
    return max(1.0, round(surge + jitter - service_bias, 2))


def _base_fare(ride_cfg: dict) -> float:
    """Compute base fare from config for the route."""
    return (
        ride_cfg["base"]
        + ride_cfg["per_km"] * config.ROUTE_DISTANCE_KM
        + ride_cfg["per_min"] * config.ROUTE_BASE_TIME_MIN
    )


def _eta(service: str, hour: float) -> int:
    """Simulate driver availability — worse during peak hours."""
    base_eta = random.randint(3, 8)
    if 7.5 <= hour <= 9.5 or 17.5 <= hour <= 19.5:
        base_eta += random.randint(3, 7)
    if service == "Uber" and random.random() < 0.4:
        base_eta = max(2, base_eta - 2)   # Uber tends to have more drivers
    return base_eta


def _travel_time(surge: float) -> int:
    """Traffic worsens during surge periods."""
    extra = int((surge - 1.0) * 15)
    return config.ROUTE_BASE_TIME_MIN + extra + random.randint(-5, 5)


# ── Service-specific fetchers ─────────────────────────────────────────────────

def _fetch_uber(hour: float) -> dict[str, PriceQuote]:
    quotes = {}
    for ride_type, ride_cfg in config.SERVICES["Uber"].items():
        surge = _surge_multiplier(hour, "Uber")
        base  = _base_fare(ride_cfg)
        quotes[ride_type] = PriceQuote(
            service="Uber",
            ride_type=ride_type,
            base_fare=round(base, 2),
            surge_multiplier=surge,
            total_fare=round(base * surge, 2),
            eta_minutes=_eta("Uber", hour),
            travel_time_minutes=_travel_time(surge),
        )
    return quotes


def _fetch_ola(hour: float) -> dict[str, PriceQuote]:
    quotes = {}
    for ride_type, ride_cfg in config.SERVICES["Ola"].items():
        surge = _surge_multiplier(hour, "Ola")
        base  = _base_fare(ride_cfg)
        quotes[ride_type] = PriceQuote(
            service="Ola",
            ride_type=ride_type,
            base_fare=round(base, 2),
            surge_multiplier=surge,
            total_fare=round(base * surge, 2),
            eta_minutes=_eta("Ola", hour),
            travel_time_minutes=_travel_time(surge),
        )
    return quotes


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_all_prices(at: datetime | None = None) -> list[PriceQuote]:
    """
    Fetch price quotes from all configured services.
    Returns a flat list of PriceQuote objects sorted by total fare.
    """
    now  = at or datetime.now()
    hour = now.hour + now.minute / 60.0

    all_quotes: list[PriceQuote] = []
    all_quotes.extend(_fetch_uber(hour).values())
    all_quotes.extend(_fetch_ola(hour).values())

    all_quotes.sort(key=lambda q: q.total_fare)
    return all_quotes
