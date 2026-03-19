"""
Configuration for the cab price monitor.
Edit this file to set your route and email credentials.
"""

# ── Route ────────────────────────────────────────────────────────────────────
ORIGIN      = "MG Road, Bangalore"
DESTINATION = "Kempegowda International Airport, Bangalore"

# Estimated baseline distance (km) and travel time (minutes) for the route.
# These are used to compute realistic base fares.
ROUTE_DISTANCE_KM  = 38
ROUTE_BASE_TIME_MIN = 55

# ── Monitoring schedule ───────────────────────────────────────────────────────
# How often to fetch and record prices (in minutes).
FETCH_INTERVAL_MIN = 5

# How often to send the "best time" email recommendation (in hours).
REPORT_INTERVAL_HR = 3

# ── Email settings ────────────────────────────────────────────────────────────
EMAIL_SENDER   = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"   # Use an App Password, not your main password
EMAIL_RECEIVER = "receiver@example.com"
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587

# ── Cab services ─────────────────────────────────────────────────────────────
# Base fares (INR) per km for each service and ride type.
# Adjust these to match real-world pricing in your city.
SERVICES = {
    "Uber": {
        "UberGo":      {"base": 50, "per_km": 11, "per_min": 1.5},
        "UberX":       {"base": 80, "per_km": 14, "per_min": 2.0},
        "UberPremier": {"base": 120, "per_km": 18, "per_min": 2.5},
    },
    "Ola": {
        "Ola Mini":    {"base": 45, "per_km": 10, "per_min": 1.2},
        "Ola Sedan":   {"base": 70, "per_km": 13, "per_min": 1.8},
        "Ola Prime":   {"base": 110, "per_km": 17, "per_min": 2.3},
    },
}

# Surge thresholds used for display labels.
SURGE_LABELS = {
    (1.0, 1.3): "Normal",
    (1.3, 1.6): "Mild surge",
    (1.6, 2.0): "Moderate surge",
    (2.0, 9.9): "High surge",
}
