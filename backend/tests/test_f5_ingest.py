"""TC_ING_01–04: ingest validation, short-gap impute, long-gap flag."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import MeterReading
from app.services.ingest import process_payload

client = TestClient(app)
SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "meter_gaps_demo.csv"


def _clear_meters():
    db = SessionLocal()
    db.query(MeterReading).delete()
    db.commit()
    db.close()


def test_tc_ing_01_accepts_valid_json_rows():
    _clear_meters()
    payload = [
        {"timestamp": "2026-02-01T00:00:00", "demand_kw": 10},
        {"timestamp": "2026-02-01T00:15:00", "demand_kw": 12},
    ]
    r = client.post("/ingest/readings/json", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] == 2
    assert body["imputed"] == 0
    assert body["rejected"] == 0


def test_tc_ing_02_rejects_bad_row_with_reason():
    r = process_payload(
        [
            {"timestamp": "2026-02-02T00:00:00", "demand_kw": 10},
            {"timestamp": "bad", "demand_kw": "x"},
        ]
    )
    assert r["rejected"] >= 1
    assert any("unparseable" in d["reason"] or "non-numeric" in d["reason"] for d in r["reject_details"])


def test_tc_ing_03_short_gap_imputed():
    # 00:30 → 01:15 = 45 min → 2 imputed steps
    r = process_payload(
        [
            {"timestamp": "2026-03-01T00:30:00", "demand_kw": 100},
            {"timestamp": "2026-03-01T01:15:00", "demand_kw": 130},
        ]
    )
    assert r["imputed"] == 2
    assert sum(1 for row in r["rows"] if row["imputed"]) == 2


def test_tc_ing_04_sample_file_counts():
    _clear_meters()
    with SAMPLE.open("rb") as f:
        r = client.post("/ingest/readings", files={"file": ("meter_gaps_demo.csv", f, "text/csv")})
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] == 7
    assert body["imputed"] == 2
    assert body["rejected"] == 1
    assert len(body["long_gaps"]) == 1
    assert body["long_gaps"][0]["gap_hours"] == 3.0
