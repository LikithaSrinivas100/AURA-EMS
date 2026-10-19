from fastapi import APIRouter

try:
    from app.schemas import HealthResponse
except ImportError:
    from schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health():
    return {"status": "ok", "service": "aura-ems-backend"}
