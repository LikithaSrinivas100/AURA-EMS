"""ORM models. Forecast / ModelRegistry keep the live API + seed path working."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

try:
    from app.db import Base
except ImportError:
    from db import Base


class EnergyLog(Base):
    """15-minute campus energy entries (Green Skills / metering trail)."""

    __tablename__ = "energy_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True, nullable=False)
    demand_kw: Mapped[float] = mapped_column(Float, nullable=False)
    academic_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    hostel_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_weekend: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_vacation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_exam_cycle: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


class ModelPerformanceMetric(Base):
    """Persisted model evaluation scores (1M1B / registry companion table)."""

    __tablename__ = "model_performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False, default="v1.0")
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    train_rows: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    test_rows: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    artifact_path: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


class Forecast(Base):
    """Dashboard inference feed (actual vs predicted) — used by seed + /forecasts."""

    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True, nullable=False)
    actual_demand_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    xgb_pred_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    lgb_pred_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_pred_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    abs_error_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


class ModelRegistry(Base):
    """Active model registry consumed by /metrics/summary."""

    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String, nullable=True)
    train_rows: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    test_rows: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True, nullable=False)
    demand_kw: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_weekend: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_vacation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_exam_cycle: Mapped[int | None] = mapped_column(Integer, nullable=True)


Forecasts = Forecast
MeterReadings = MeterReading
EnergyLogs = EnergyLog
ModelPerformanceMetrics = ModelPerformanceMetric
