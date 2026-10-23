"""Pydantic v2 response schemas for the AURA-EMS API."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseSchema):
    status: str
    service: str


class MetricsSummaryResponse(BaseSchema):
    active_model: str
    rmse: float
    mape: float
    mae: float
    train_rows: int
    test_rows: int


class ForecastItem(BaseSchema):
    ts: datetime
    actual_demand_kw: Optional[float] = None
    best_pred_kw: float
    xgb_pred_kw: Optional[float] = None
    lgb_pred_kw: Optional[float] = None


class ForecastsResponse(BaseSchema):
    count: int
    items: List[ForecastItem]


class PeakItem(BaseSchema):
    ts: datetime
    best_pred_kw: float
    risk_level: str


class PeaksResponse(BaseSchema):
    items: List[PeakItem]


class DataRangeResponse(BaseSchema):
    min_ts: datetime
    max_ts: datetime
    count: int


class PredictRequest(BaseSchema):
    """Single-point on-demand prediction using the published feature contract."""

    features: Dict[str, float]


class PredictResponse(BaseSchema):
    pred_kw: float
    model: str = "total"


INDIA_GRID_EF_KG_PER_KWH = 0.71
EDU_TARIFF_INR_PER_KWH = 8.50
HIGH_RISK_KW = 350.0


class CarbonImpactResponse(BaseSchema):
    hours: int
    grid_emission_factor_kg_per_kwh: float = Field(default=INDIA_GRID_EF_KG_PER_KWH)
    tariff_inr_per_kwh: float = Field(default=EDU_TARIFF_INR_PER_KWH)
    forecast_energy_kwh: float
    baseline_peak_kw: float
    shaved_peak_kw: float
    energy_avoided_kwh: float
    co2_avoided_kg: float
    cost_saved_inr: float
    trees_equivalent: float
    notes: str
