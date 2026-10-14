import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import db_manager, DatabaseUnavailableException
from backend.app.routes import (
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
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
