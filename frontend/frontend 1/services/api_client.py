"""Thin HTTP client for the AURA-EMS backend API (owned by Anushka).

Every function returns a (data, error) tuple:
    - data:  parsed JSON payload on success, else None
    - error: None on success, else a short human-readable string

Callers (app.py) should check `error` first and render the app's error
state instead of letting an exception crash the dashboard.
"""
from typing import Any, Dict, Optional, Tuple

import requests

from services.config import API_BASE_URL, REQUEST_TIMEOUT


def _get(path: str, params: Optional[dict] = None) -> Tuple[Optional[Any], Optional[str]]:
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Backend unavailable. Please start FastAPI on port 8000."
    except requests.exceptions.Timeout:
        return None, "Backend request timed out."
    except requests.exceptions.HTTPError as exc:
        return None, f"Backend returned an error: {exc}"
    except ValueError:
        return None, "Backend returned an invalid (non-JSON) response."


def get_health() -> Tuple[Optional[Dict], Optional[str]]:
    """GET /health -> {"status": "ok", "service": "aura-ems-backend"}"""
    return _get("/health")


def get_metrics() -> Tuple[Optional[Dict], Optional[str]]:
    """GET /metrics/summary -> active_model, rmse, mape, mae, train_rows, test_rows"""
    return _get("/metrics/summary")


def get_forecasts(start: Optional[str] = None, end: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """GET /forecasts?start=...&end=... -> {"count": int, "items": [...]}"""
    params = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _get("/forecasts", params=params)


def get_peaks(limit: int = 10) -> Tuple[Optional[Dict], Optional[str]]:
    """GET /forecasts/peaks?limit=10 -> {"items": [...]}"""
    return _get("/forecasts/peaks", params={"limit": limit})
