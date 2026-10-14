import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import AnomaliesResponse
from backend.app.services.anomaly_service import anomaly_service

logger = logging.getLogger("energy_backend.routes.anomalies")
router = APIRouter(prefix="/api/anomalies", tags=["Anomaly Detection"])


@router.get("", response_model=AnomaliesResponse)
def get_energy_anomalies():
    """
    Detect abnormal campus consumption using Scikit-learn Isolation Forest
    and statistical 2-sigma thresholds, returning actionable feature-attributed explanations.
    """
    try:
        return anomaly_service.detect_anomalies()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error detecting energy anomalies: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )
