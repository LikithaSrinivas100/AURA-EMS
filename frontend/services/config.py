"""Configuration for the AURA-EMS frontend dashboard.

Set API_BASE_URL in the environment when the backend is hosted remotely.
"""

import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
if not API_BASE_URL.startswith(("http://", "https://")):
    API_BASE_URL = f"https://{API_BASE_URL}"
REQUEST_TIMEOUT = 30  # seconds; the first 7-day forecast request takes ~10s

DEFAULT_PEAKS_LIMIT = 10

RISK_COLORS = {
    "HIGH": "#e63946",
    "MEDIUM": "#f4a261",
    "LOW": "#2a9d8f",
}
