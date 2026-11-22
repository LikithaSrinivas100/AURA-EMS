from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.db import Base, engine
    from app import models  # noqa: F401
    from app.routers import forecasts, health, ingest, metrics, replay
except ImportError:
    from db import Base, engine
    import models  # noqa: F401
    from routers import forecasts, health, ingest, metrics, replay


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # additive column for F5 on existing SQLite files
    from sqlalchemy import text

    with engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(meter_readings)")).fetchall()]
        if "imputed" not in cols:
            conn.execute(text("ALTER TABLE meter_readings ADD COLUMN imputed BOOLEAN DEFAULT 0"))
    try:
        from app.services.forecaster import warm_models
    except ImportError:
        from services.forecaster import warm_models
    warm_models()
    yield


app = FastAPI(title="AURA-EMS Backend API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(forecasts.router)
app.include_router(replay.router)
app.include_router(ingest.router)
