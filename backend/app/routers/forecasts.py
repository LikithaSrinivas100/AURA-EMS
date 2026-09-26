from datetime import datetime, timedelta
from typing import Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from app.db import get_db
    from app.models import Forecast
    from app.schemas import ForecastItem, ForecastsResponse, PeakItem, PeaksResponse
except ImportError:
    from db import get_db
    from models import Forecast
    from schemas import ForecastItem, ForecastsResponse, PeakItem, PeaksResponse

router = APIRouter()


@router.get("/forecasts/peaks", response_model=PeaksResponse)
@router.get("/peaks", response_model=PeaksResponse)
def get_peaks(
    limit: int = Query(10, ge=1, description="Number of peak rows to return"),
    db: Session = Depends(get_db)
):
    all_values = [
        val[0] for val in db.query(Forecast.best_pred_kw)
        .filter(Forecast.best_pred_kw.isnot(None))
        .all()
    ]

    if not all_values:
        return PeaksResponse(items=[])

    p90 = float(np.percentile(all_values, 90))
    p75 = float(np.percentile(all_values, 75))

    def calculate_risk(pred_val: float) -> str:
        if pred_val >= p90:
            return "HIGH"
        elif pred_val >= p75:
            return "MEDIUM"
        return "LOW"

    top_rows = (
        db.query(Forecast)
        .filter(Forecast.best_pred_kw.isnot(None))
        .order_by(Forecast.best_pred_kw.desc())
        .limit(limit)
        .all()
    )

    items = [
        PeakItem(
            ts=row.ts,
            best_pred_kw=row.best_pred_kw,
            risk_level=calculate_risk(row.best_pred_kw)
        )
        for row in top_rows
    ]

    return PeaksResponse(items=items)


@router.get("/forecasts", response_model=ForecastsResponse)
@router.get("", response_model=ForecastsResponse)
def get_forecasts(
    start: Optional[str] = Query(None, description="Start timestamp filter"),
    end: Optional[str] = Query(None, description="End timestamp filter"),
    db: Session = Depends(get_db)
):
    query = db.query(Forecast)

    start_dt = None
    end_dt = None

    if start:
        try:
            start_dt = pd.to_datetime(start).to_pydatetime()
        except Exception:
            start_dt = None

    if end:
        try:
            end_dt = pd.to_datetime(end).to_pydatetime()
        except Exception:
            end_dt = None

    if start_dt and end_dt:
        query = query.filter(Forecast.ts >= start_dt, Forecast.ts <= end_dt)
    elif start_dt:
        query = query.filter(Forecast.ts >= start_dt)
    elif end_dt:
        query = query.filter(Forecast.ts <= end_dt)
    else:
        # If no start/end provided, return last 48 hours of data
        latest_ts = db.query(func.max(Forecast.ts)).scalar()
        if latest_ts:
            cutoff = latest_ts - timedelta(hours=48)
            query = query.filter(Forecast.ts >= cutoff)

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
