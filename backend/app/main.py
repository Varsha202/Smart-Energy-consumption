import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import sys
from pathlib import Path

# Support both package-relative imports and direct script execution
if __package__ in (None, ""):
    _backend_dir = Path(__file__).resolve().parent.parent
    _root_dir = _backend_dir.parent
    for _p in (str(_root_dir), str(_backend_dir)):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from app.config import settings
    from app.database import db_manager, DatabaseUnavailableException
    from app.routes import (
        health_router,
        energy_router,
        analytics_router,
        forecast_router,
        anomalies_router,
        recommendations_router
    )
else:
    from .config import settings
    from .database import db_manager, DatabaseUnavailableException
    from .routes import (
        health_router,
        energy_router,
        analytics_router,
        forecast_router,
        anomalies_router,
        recommendations_router
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("energy_backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for MongoDB connection setup and teardown."""
    logger.info("Starting up Smart Campus Energy Backend...")
    db_manager.connect()
    yield
    logger.info("Shutting down Smart Campus Energy Backend...")
    db_manager.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "AI-Driven Smart Campus Energy Consumption Analytics System API.\n\n"
        "Provides REST endpoints for energy ingestion, historical time-series analytics, "
        "facility breakdowns, machine learning forecasting, statistical anomaly detection, "
        "and evidence-based energy conservation recommendations."
    ),
    lifespan=lifespan
)

# Configure CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DatabaseUnavailableException)
async def database_unavailable_exception_handler(request: Request, exc: DatabaseUnavailableException):
    """Handle database connection exceptions cleanly with standard JSON response."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "DatabaseUnavailable",
            "message": str(exc),
            "detail": "MongoDB is currently unavailable. Please verify MONGODB_URI and service status."
        }
    )


# Register API Routers
app.include_router(health_router)
app.include_router(energy_router)
app.include_router(analytics_router)
app.include_router(forecast_router)
app.include_router(anomalies_router)
app.include_router(recommendations_router)


if __name__ == "__main__":
    import uvicorn
    # Auto-detect module name based on whether 'backend' package was imported
    app_module = "backend.app.main:app" if "backend" in sys.modules else "app.main:app"
    uvicorn.run(
        app_module,
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
