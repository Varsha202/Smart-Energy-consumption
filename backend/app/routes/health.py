from datetime import datetime
from fastapi import APIRouter
from ..config import settings
from ..database import db_manager
from ..models.schemas import ServiceStatusResponse, HealthResponse

router = APIRouter(tags=["Health & Status"])


@router.get("/", response_model=ServiceStatusResponse)
def get_service_status():
    """Root endpoint returning service status and version."""
    return ServiceStatusResponse(
        message="Smart Campus Energy Backend API",
        status="running",
        version=settings.VERSION
    )


@router.get("/health", response_model=HealthResponse)
def get_health_check():
    """
    Health check endpoint reporting application and MongoDB connectivity status.
    Returns status:
    - 'healthy' when database is connected
    - 'degraded' when database is unreachable but local fallback is available
    """
    is_db_connected = db_manager.ping()
    
    if is_db_connected:
        status = "healthy"
        db_status = "connected"
        details = "All services operational and connected to MongoDB."
    else:
        status = "degraded"
        db_status = "disconnected"
        details = "MongoDB is unreachable. Backend is operating with local dataset fallback mode."

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        version=settings.VERSION,
        database=db_status,
        database_name=settings.DATABASE_NAME,
        collection_name=settings.ENERGY_COLLECTION,
        details=details
    )
