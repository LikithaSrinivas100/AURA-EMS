"""Frontend config — API URL + Calculated Caliber risk chip colors."""
import os

_raw = (
    os.getenv("API_BASE_URL")
    or os.getenv("AURA_BACKEND_URL")
    or "http://127.0.0.1:8000"
).rstrip("/")
API_BASE_URL = _raw if _raw.startswith("http") else f"https://{_raw}"
REQUEST_TIMEOUT = 180  # ahead forecast on Render free tier can exceed 60s

DEFAULT_PEAKS_LIMIT = 10

# Design system risk chips (not decorative)
RISK_COLORS = {
    "HIGH": "#B91C1C",
    "MEDIUM": "#C2410C",
    "LOW": "#15803D",
}
