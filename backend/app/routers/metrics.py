import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.db import get_db
    from app.models import ModelRegistry
    from app.schemas import MetricsSummaryResponse
    from app.services.forecaster import parse_zone
except ImportError:
    from db import get_db
    from models import ModelRegistry
    from schemas import MetricsSummaryResponse
    from services.forecaster import parse_zone

router = APIRouter()

_ML_METRICS = (
    Path(__file__).resolve().parents[3] / "ML_Implementation" / "outputs" / "metrics.json"
)
_ZONE_TARGET = {
    "campus": "Total_Campus_Demand_kW",
    "academic": "Academic_Demand_kW",
    "hostels": "Hostel_Demand_kW",
}


def _ml_payload() -> dict:
    if not _ML_METRICS.is_file():
        return {}
    try:
        return json.loads(_ML_METRICS.read_text(encoding="utf-8"))
    except Exception:
        return {}


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def get_metrics_summary(zone: str = Query("campus"), db: Session = Depends(get_db)):
    try:
        parse_zone(zone)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    z = (zone or "campus").strip().lower()
    active_model = db.query(ModelRegistry).filter(ModelRegistry.is_active == True).first()
    if not active_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active model found")
    payload = _ml_payload()
    peak = payload.get("peak_alert") or {}
    zm = (payload.get("zone_metrics") or {}).get(z) or {}
    rmse = float(zm["rmse"]) if "rmse" in zm else (active_model.rmse if active_model.rmse is not None else 0.0)
    mae = float(zm["mae"]) if "mae" in zm else (active_model.mae if active_model.mae is not None else 0.0)
    mape = (
        float(zm["mape_percent"])
        if "mape_percent" in zm
        else (active_model.mape if active_model.mape is not None else 0.0)
    )
    return MetricsSummaryResponse(
        active_model=active_model.model_name if z == "campus" else f"XGBoost-{z}",
        rmse=rmse,
        mape=mape,
        mae=mae,
        train_rows=active_model.train_rows if getattr(active_model, "train_rows", None) is not None else 0,
        test_rows=active_model.test_rows if getattr(active_model, "test_rows", None) is not None else 0,
        target=_ZONE_TARGET[z],
        interval_minutes=15,
        max_horizon_hours=168,
        data_source="simulated",
        peak_alert_precision=peak.get("precision") if z == "campus" else None,
        peak_alert_recall=peak.get("recall") if z == "campus" else None,
        peak_alert_f1=peak.get("f1") if z == "campus" else None,
        peak_alert_false_alarm_rate=peak.get("false_alarm_rate") if z == "campus" else None,
        peak_alert_threshold_kw=peak.get("threshold_kw") if z == "campus" else None,
    )
