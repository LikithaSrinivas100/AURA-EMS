"""Thin HTTP client for the AURA-EMS backend API."""
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
    return _get("/health")


def get_metrics() -> Tuple[Optional[Dict], Optional[str]]:
    return _get("/metrics/summary")


def get_data_range() -> Tuple[Optional[Dict], Optional[str]]:
    return _get("/forecasts/range")


def get_forecasts(start: Optional[str] = None, end: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    params = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _get("/forecasts", params=params)


def get_today_peak() -> Tuple[Optional[Dict], Optional[str]]:
    data, err = _get("/forecasts/today-peak")
    if data is not None:
        return data, None
    return _get("/api/v1/forecasts/today-peak")


def get_forecast_ahead(
    hours: int = 24,
    as_of: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Tuple[Optional[Dict], Optional[str]]:
    params = {"hours": hours}
    if as_of:
        params["as_of"] = as_of
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    data, err = _get("/forecasts/ahead", params=params)
    # One retry at 24h if a long horizon times out on cold Render
    if err and "timed out" in err.lower() and hours > 24:
        params["hours"] = 24
        data, err2 = _get("/forecasts/ahead", params=params)
        if data is not None:
            return data, None
        return None, err2 or err
    return data, err


def get_carbon(
    hours: int = 24,
    as_of: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Tuple[Optional[Dict], Optional[str]]:
    params = {"hours": hours}
    if as_of:
        params["as_of"] = as_of
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _get("/forecasts/carbon", params=params)


def get_peaks(
    limit: int = 10, start: Optional[str] = None, end: Optional[str] = None
) -> Tuple[Optional[Dict], Optional[str]]:
    params = {"limit": limit}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _get("/forecasts/peaks", params=params)
