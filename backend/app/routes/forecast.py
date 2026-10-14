import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import ForecastResponse
from backend.app.services.forecast_service import forecast_service

logger = logging.getLogger("energy_backend.routes.forecast")
router = APIRouter(prefix="/api/forecast", tags=["Forecasting"])


@router.get("", response_model=ForecastResponse)
def get_three_month_forecast():
    """
    Generate 3-month daily energy consumption forecast with confidence intervals.
    Includes time-aware validation metrics against a day-of-week baseline model
    and explicit disclosures regarding 31-day data limitations.
    """
    try:
        return forecast_service.generate_three_month_forecast()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error generating energy forecast: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation failed: {str(e)}"
        )
