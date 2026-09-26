from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    # Enable reading directly from SQLAlchemy model objects (orm_mode in Pydantic v2)
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
