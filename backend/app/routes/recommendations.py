import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import RecommendationsResponse
from backend.app.services.recommendation_service import recommendation_service

logger = logging.getLogger("energy_backend.routes.recommendations")
router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.get("", response_model=RecommendationsResponse)
def get_energy_saving_recommendations():
    """
    Generate evidence-based energy conservation recommendations derived from
    empirical consumption patterns, HVAC loads, and generator dispatches.
    """
    try:
        return recommendation_service.generate_recommendations()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error generating energy recommendations: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )
