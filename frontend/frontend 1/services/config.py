"""Configuration for the AURA-EMS frontend dashboard.

Change API_BASE_URL here (and nowhere else) if Anushka's backend
ever runs on a different host/port.
"""

API_BASE_URL = "http://127.0.0.1:8001"
REQUEST_TIMEOUT = 10  # seconds

DEFAULT_PEAKS_LIMIT = 10

RISK_COLORS = {
    "HIGH": "#e63946",
    "MEDIUM": "#f4a261",
    "LOW": "#2a9d8f",
}
