"""TC_F2: zone param validation + zone_metrics in metrics.json."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.forecaster import parse_zone

client = TestClient(app)


def test_parse_zone_ok():
    assert parse_zone("campus") == "total"
    assert parse_zone("academic") == "academic"
    assert parse_zone("hostels") == "hostel"


def test_parse_zone_bad():
    with pytest.raises(ValueError):
        parse_zone("labs")


def test_forecasts_invalid_zone_422():
    r = client.get("/forecasts", params={"zone": "labs"})
    assert r.status_code == 422


def test_peaks_invalid_zone_422():
    r = client.get("/forecasts/peaks", params={"zone": "xyz"})
    assert r.status_code == 422


def test_metrics_json_has_zone_metrics():
    p = Path(__file__).resolve().parents[2] / "ML_Implementation" / "outputs" / "metrics.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    zm = data["zone_metrics"]
    for z in ("campus", "academic", "hostels"):
        assert {"rmse", "mae", "mape_percent"} <= set(zm[z])
