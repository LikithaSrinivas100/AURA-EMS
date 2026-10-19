"""Configuration for the AURA-EMS frontend dashboard.

Local default is port 8000. On Render/hosting, set env var API_BASE_URL
(or AURA_BACKEND_URL) to the public backend URL.
"""
import os

_raw = (
    os.getenv("API_BASE_URL")
    or os.getenv("AURA_BACKEND_URL")
    or "http://127.0.0.1:8000"
).rstrip("/")
# Render Blueprint may inject host without scheme (aura-ems-backend.onrender.com)
API_BASE_URL = _raw if _raw.startswith("http") else f"https://{_raw}"
REQUEST_TIMEOUT = 30  # seconds; the first 7-day forecast request takes ~10s

DEFAULT_PEAKS_LIMIT = 10

RISK_COLORS = {
    "HIGH": "#e63946",
    "MEDIUM": "#f4a261",
    "LOW": "#2a9d8f",
}
