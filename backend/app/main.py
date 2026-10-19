from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.db import Base, engine
    from app import models  # noqa: F401
    from app.routers import forecasts, health, metrics
except ImportError:
    from db import Base, engine
    import models  # noqa: F401
    from routers import forecasts, health, metrics


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
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
