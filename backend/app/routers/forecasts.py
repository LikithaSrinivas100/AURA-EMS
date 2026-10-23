from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from app.db import get_db
    from app.models import Forecast
    from app.schemas import (
        CarbonImpactResponse,
        DataRangeResponse,
        EDU_TARIFF_INR_PER_KWH,
        ForecastItem,
        ForecastsResponse,
        INDIA_GRID_EF_KG_PER_KWH,
        PeakItem,
        PeaksResponse,
        PredictRequest,
        PredictResponse,
    )
    from app.services.forecaster import count_calendar_intervals, forecast_ahead, predict_one
    from app.services.weather import today_peak
except ImportError:
    from db import get_db
    from models import Forecast
    from schemas import (
        CarbonImpactResponse,
        DataRangeResponse,
        EDU_TARIFF_INR_PER_KWH,
        ForecastItem,
        ForecastsResponse,
        INDIA_GRID_EF_KG_PER_KWH,
        PeakItem,
        PeaksResponse,
        PredictRequest,
        PredictResponse,
    )
    from services.forecaster import count_calendar_intervals, forecast_ahead, predict_one
    from services.weather import today_peak

router = APIRouter()
_INTERVAL_HOURS = 0.25
_TREE_KG_CO2_PER_YEAR = 21.0


def _parse_ts(value: Optional[str]):
    if not value:
        return None
    ts = pd.to_datetime(str(value).replace("Z", ""), errors="coerce")
    if pd.isna(ts):
        return None
    if getattr(ts, "tz", None) is not None:
        ts = ts.tz_convert("Asia/Kolkata").tz_localize(None)
    return ts.to_pydatetime()


@router.get("/forecasts/range", response_model=DataRangeResponse)
def get_data_range(db: Session = Depends(get_db)):
    mn, mx, n = db.query(func.min(Forecast.ts), func.max(Forecast.ts), func.count(Forecast.id)).one()
    if not mn or not mx:
        raise HTTPException(status_code=404, detail="No forecast rows seeded")
    return DataRangeResponse(min_ts=mn, max_ts=mx, count=int(n))


@router.get("/forecasts/ahead")
def get_forecast_ahead(
    hours: int = Query(24, ge=1, le=168),
    as_of: Optional[str] = Query(None, description="Optional anchor timestamp; forecast starts after this row"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    as_of_dt = _parse_ts(as_of)
    try:
        payload = forecast_ahead(hours, as_of_dt.isoformat() if as_of_dt else (as_of or ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    df = pd.DataFrame(payload.get("items") or [])
    if not df.empty and "ts" in df:
        df["ts"] = pd.to_datetime(df["ts"])
        df = df.set_index("ts")
    start_dt, end_dt = _parse_ts(start), _parse_ts(end)
    if start_dt and end_dt:
        exam, vac = count_calendar_intervals(start_dt, end_dt)
    elif not df.empty:
        exam = int(df["is_exam"].sum()) if "is_exam" in df.columns else 0
        vac = int(df["is_vacation"].sum()) if "is_vacation" in df.columns else 0
    else:
        exam = vac = 0
    payload["exam_intervals"] = exam
    payload["vacation_intervals"] = vac
    return payload


@router.get("/forecasts/today-peak")
@router.get("/api/v1/forecasts/today-peak")
def get_today_peak():
    try:
        return today_peak()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"today-peak failed: {exc}") from exc


@router.get("/forecasts/carbon", response_model=CarbonImpactResponse)
def get_carbon_impact(
    start: Optional[str] = Query(None, description="Start of selected filter window"),
    end: Optional[str] = Query(None, description="End of selected filter window"),
    hours: int = Query(24, ge=1, le=168),
    as_of: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Carbon impact for the selected date range (preferred), else ahead forecast."""
    start_dt, end_dt = _parse_ts(start), _parse_ts(end)
    totals: list[float] = []
    source = "selected date range"

    if start_dt or end_dt:
        q = db.query(Forecast.best_pred_kw).filter(Forecast.best_pred_kw.isnot(None))
        if start_dt:
            q = q.filter(Forecast.ts >= start_dt)
        if end_dt:
            q = q.filter(Forecast.ts <= end_dt)
        totals = [float(v[0]) for v in q.all()]
        if start_dt and end_dt:
            hours = max(1, int((end_dt - start_dt).total_seconds() // 3600) or 1)
    else:
        try:
            payload = forecast_ahead(hours, as_of or "")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        totals = [float(i["total_kw"]) for i in (payload.get("items") or [])]
        source = "ahead forecast"

    if not totals:
        return CarbonImpactResponse(
            hours=hours,
            forecast_energy_kwh=0.0,
            baseline_peak_kw=0.0,
            shaved_peak_kw=0.0,
            energy_avoided_kwh=0.0,
            co2_avoided_kg=0.0,
            cost_saved_inr=0.0,
            trees_equivalent=0.0,
            notes=f"No rows in {source}. Pick dates inside available history.",
        )

    p90, p75 = float(np.percentile(totals, 90)), float(np.percentile(totals, 75))
    shaved = [min(v, p75) if v >= p90 else v for v in totals]
    forecast_energy_kwh = sum(totals) * _INTERVAL_HOURS
    energy_avoided = max(0.0, (sum(totals) - sum(shaved)) * _INTERVAL_HOURS)
    co2 = energy_avoided * INDIA_GRID_EF_KG_PER_KWH
    cost = energy_avoided * EDU_TARIFF_INR_PER_KWH
    return CarbonImpactResponse(
        hours=hours,
        forecast_energy_kwh=round(forecast_energy_kwh, 2),
        baseline_peak_kw=round(max(totals), 2),
        shaved_peak_kw=round(max(shaved), 2),
        energy_avoided_kwh=round(energy_avoided, 2),
        co2_avoided_kg=round(co2, 2),
        cost_saved_inr=round(cost, 2),
        trees_equivalent=round(co2 / _TREE_KG_CO2_PER_YEAR, 2),
        notes=(
            f"Based on {source} ({len(totals)} intervals). "
            f"Indian grid EF {INDIA_GRID_EF_KG_PER_KWH} kg CO2/kWh, "
            f"tariff ₹{EDU_TARIFF_INR_PER_KWH}/kWh. HIGH (≥P90) capped at P75."
        ),
    )


@router.post("/predict", response_model=PredictResponse)
def post_predict(body: PredictRequest, zone: str = Query("total")):
    try:
        return PredictResponse(pred_kw=round(predict_one(body.features, zone=zone), 2), model=zone)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/forecasts/peaks", response_model=PeaksResponse)
def get_peaks(
    limit: int = Query(10, ge=1, le=50),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Top peaks using rank thresholds (Render-safe; no full-series load)."""
    start_dt, end_dt = _parse_ts(start), _parse_ts(end)
    base = db.query(Forecast).filter(Forecast.best_pred_kw.isnot(None))
    if start_dt:
        base = base.filter(Forecast.ts >= start_dt)
    if end_dt:
        base = base.filter(Forecast.ts <= end_dt)

    total = base.count()
    if total == 0:
        return PeaksResponse(items=[])

    ordered = base.order_by(Forecast.best_pred_kw.desc())
    p90_row = ordered.offset(max(0, int(total * 0.10))).limit(1).first()
    p75_row = ordered.offset(max(0, int(total * 0.25))).limit(1).first()
    p90 = float(p90_row.best_pred_kw) if p90_row else 0.0
    p75 = float(p75_row.best_pred_kw) if p75_row else 0.0

    def risk(v: float) -> str:
        if v >= p90:
            return "HIGH"
        if v >= p75:
            return "MEDIUM"
        return "LOW"

    top_rows = ordered.limit(limit).all()
    return PeaksResponse(
        items=[PeakItem(ts=r.ts, best_pred_kw=r.best_pred_kw, risk_level=risk(r.best_pred_kw)) for r in top_rows]
    )


@router.get("/forecasts", response_model=ForecastsResponse)
def get_forecasts(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Forecast)
    start_dt, end_dt = _parse_ts(start), _parse_ts(end)
    if start_dt and end_dt:
        query = query.filter(Forecast.ts >= start_dt, Forecast.ts <= end_dt)
    elif start_dt:
        query = query.filter(Forecast.ts >= start_dt)
    elif end_dt:
        query = query.filter(Forecast.ts <= end_dt)
    else:
        latest_ts = db.query(func.max(Forecast.ts)).scalar()
        if latest_ts:
            query = query.filter(Forecast.ts >= latest_ts - timedelta(hours=48))

    records = query.order_by(Forecast.ts.asc()).all()
    items = [
        ForecastItem(
            ts=row.ts,
            actual_demand_kw=row.actual_demand_kw,
            best_pred_kw=row.best_pred_kw,
            xgb_pred_kw=row.xgb_pred_kw,
            lgb_pred_kw=row.lgb_pred_kw,
        )
        for row in records
    ]
    return ForecastsResponse(count=len(items), items=items)
