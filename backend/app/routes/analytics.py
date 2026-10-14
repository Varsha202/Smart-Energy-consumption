import logging
from fastapi import APIRouter, HTTPException, status
from ..models.schemas import (
    AnalyticsSummaryResponse,
    DailyAnalyticsResponse,
    FacilitiesResponse
)
from ..services.analytics_service import analytics_service

logger = logging.getLogger("energy_backend.routes.analytics")
router = APIRouter(prefix="/api/analytics", tags=["Analytics & KPIs"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary():
    """
    Returns campus energy KPIs including total consumption, daily average,
    peak day, source breakdown, facility breakdown, emissions, and cost.
    """
    try:
        return analytics_service.get_summary()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error generating analytics summary: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.get("/daily", response_model=DailyAnalyticsResponse)
def get_daily_analytics():
    """
    Returns chronological daily time-series formatted for Plotly line and bar charts.
    """
    try:
        return analytics_service.get_daily_series()
    except Exception as e:
        logger.error("Error generating daily analytics: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily series: {str(e)}"
        )


@router.get("/facilities", response_model=FacilitiesResponse)
def get_facilities_breakdown():
    """
    Returns facility-level metrics, ranking, percentages, daily averages, and peak days.
    """
    try:
        return analytics_service.get_facilities_breakdown()
    except Exception as e:
        logger.error("Error generating facilities analytics: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate facilities breakdown: {str(e)}"
        )
