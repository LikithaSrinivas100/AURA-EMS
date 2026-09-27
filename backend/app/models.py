from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func

try:
    from app.db import Base
except ImportError:
    from db import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, unique=True, index=True, nullable=False)
    actual_demand_kw = Column(Float, nullable=True)
    xgb_pred_kw = Column(Float, nullable=True)
    lgb_pred_kw = Column(Float, nullable=True)
    best_pred_kw = Column(Float, nullable=True)
    abs_error_kw = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    artifact_path = Column(String, nullable=True)
    train_rows = Column(Integer, nullable=True, default=0)
    test_rows = Column(Integer, nullable=True, default=0)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, unique=True, index=True, nullable=False)
    demand_kw = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=True)
    hour = Column(Integer, nullable=True)
    day_of_week = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    is_weekend = Column(Integer, nullable=True)
    is_vacation = Column(Integer, nullable=True)
    is_exam_cycle = Column(Integer, nullable=True)


# Aliases to support singular or plural naming conventions
Forecasts = Forecast
MeterReadings = MeterReading
