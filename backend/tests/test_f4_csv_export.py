"""TC_F4: CSV export headers + zone filter honour."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_forecasts_csv_header_and_units():
    r = client.get("/forecasts/export.csv", params={"zone": "campus"})
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    lines = r.text.strip().splitlines()
    assert lines[0] == "timestamp_iso,actual_demand_kw,predicted_kw,xgb_pred_kw,lgb_pred_kw,zone"


def test_peaks_csv_has_action_column():
    r = client.get("/forecasts/peaks/export.csv", params={"zone": "campus", "limit": 5})
    assert r.status_code == 200
    header = r.text.strip().splitlines()[0]
    assert header == "timestamp_iso,predicted_kw,risk_level,recommended_action,zone"


def test_export_invalid_zone_422():
    assert client.get("/forecasts/export.csv", params={"zone": "labs"}).status_code == 422
