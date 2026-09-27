from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.db import get_db
    from app.models import ModelRegistry
    from app.schemas import MetricsSummaryResponse
except ImportError:
    from db import get_db
    from models import ModelRegistry
    from schemas import MetricsSummaryResponse

router = APIRouter()


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
@router.get("/summary", response_model=MetricsSummaryResponse)
def get_metrics_summary(db: Session = Depends(get_db)):
    active_model = db.query(ModelRegistry).filter(ModelRegistry.is_active == True).first()
    if not active_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active model found"
        )
    return MetricsSummaryResponse(
        active_model=active_model.model_name,
        rmse=active_model.rmse if active_model.rmse is not None else 0.0,
        mape=active_model.mape if active_model.mape is not None else 0.0,
        mae=active_model.mae if active_model.mae is not None else 0.0,
        train_rows=active_model.train_rows if getattr(active_model, "train_rows", None) is not None else 0,
        test_rows=active_model.test_rows if getattr(active_model, "test_rows", None) is not None else 0,
    )
