from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.db import Base, engine
    from app.routers import forecasts, health, metrics
except ImportError:
    from db import Base, engine
    from routers import forecasts, health, metrics

app = FastAPI(title="AURA-EMS Backend API")

# Configure CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Automatically create all DB tables on startup
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


# Create tables on import as well
Base.metadata.create_all(bind=engine)

# Filter empty router paths if any and register all 3 routers
for router_module in (health.router, metrics.router, forecasts.router):
    router_module.routes = [route for route in router_module.routes if getattr(route, "path", "") != ""]

app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(forecasts.router)
