"""POST /ingest/readings — CSV or JSON meter feed (demo path, not live BESCOM)."""
from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

try:
    from app.db import get_db
    from app.models import MeterReading
    from app.services.ingest import process_payload
except ImportError:
    from db import get_db
    from models import MeterReading
    from services.ingest import process_payload

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _commit_rows(db: Session, result: dict) -> dict:
    try:
        for row in result["rows"]:
            db.add(
                MeterReading(
                    ts=row["ts"],
                    demand_kw=float(row["demand_kw"]),
                    imputed=bool(row.get("imputed", False)),
                )
            )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB write failed: {exc}") from exc
    return {
        "accepted": result["accepted"],
        "imputed": result["imputed"],
        "rejected": result["rejected"],
        "long_gaps": result["long_gaps"],
        "reject_details": result["reject_details"],
        "notes": "Demo ingestion path on sample/uploaded data — not a live BESCOM or BMS feed.",
    }


def _existing(db: Session) -> set:
    return {r[0] for r in db.query(MeterReading.ts).all()}


@router.post("/readings")
async def ingest_readings(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = (await file.read()).decode("utf-8-sig")
    name = (file.filename or "").lower()
    if name.endswith(".json"):
        raw_rows = json.loads(raw)
    else:
        raw_rows = [dict(r) for r in csv.DictReader(io.StringIO(raw))]
    if not isinstance(raw_rows, list) or not raw_rows:
        raise HTTPException(status_code=400, detail="No readings found in payload")
    return _commit_rows(db, process_payload(raw_rows, existing_ts=_existing(db)))


@router.post("/readings/json")
def ingest_readings_json(payload: list[dict], db: Session = Depends(get_db)):
    if not payload:
        raise HTTPException(status_code=400, detail="Empty payload")
    return _commit_rows(db, process_payload(payload, existing_ts=_existing(db)))
