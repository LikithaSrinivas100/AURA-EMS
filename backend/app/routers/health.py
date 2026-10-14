from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

try:
    from app.db import get_db
    from app.models import Forecast, ModelRegistry, MeterReading
    from app.schemas import HealthResponse
except ImportError:
    from db import get_db
    from models import Forecast, ModelRegistry, MeterReading
    from schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
@router.get("", response_model=HealthResponse)
def get_health():
    return {"status": "ok", "service": "aura-ems-backend"}
