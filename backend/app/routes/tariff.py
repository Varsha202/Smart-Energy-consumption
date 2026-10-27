import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from ..models.schemas import (
    TariffConfig,
    TariffCalculationRequest,
    TariffCalculationResult,
)
from ..services.tariff_service import tariff_service
from ..services.energy_service import energy_service

logger = logging.getLogger("energy_backend.routes.tariff")
router = APIRouter(prefix="/api/tariff", tags=["Electricity Tariff"])


@router.get("", response_model=Dict[str, Any])
def get_tariff_configuration():
    """
    Returns current active tariff configuration, editable slab definitions,
    and current campus-level progressive bill calculation.
    """
    try:
        config = tariff_service.get_active_config()

        # Compute current campus estimated total bill based on loaded records
        campus_kwh = 0.0
        df = energy_service.get_all_records_as_df()
        if not df.empty and "total" in df.columns:
            campus_kwh = float(df["total"].sum())

        calc_result = tariff_service.calculate_bill(campus_kwh, config=config)

        return {
            "config": config.model_dump(),
            "campus_consumption_kwh": round(campus_kwh, 2),
            "campus_calculation": calc_result.model_dump(),
        }
    except Exception as e:
        logger.error("Error retrieving tariff configuration: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tariff configuration: {str(e)}",
        )


@router.put("", response_model=TariffConfig)
def update_tariff_configuration(new_config: TariffConfig):
    """
    Update, validate, and persist electricity tariff configuration.
    Validates boundary contiguity, non-negativity, and billing mode.
    """
    try:
        updated = tariff_service.update_config(new_config)
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Error saving tariff configuration: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save tariff configuration: {str(e)}",
        )


@router.post("/calculate", response_model=TariffCalculationResult)
def calculate_tariff_bill(payload: TariffCalculationRequest):
    """
    Progressive decimal-safe tariff calculator for an arbitrary consumption level.
    Optionally evaluates against a custom uncommitted configuration.
    """
    try:
        return tariff_service.calculate_bill(
            consumption_kwh=payload.consumption_kwh,
            config=payload.config,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Error calculating tariff bill: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tariff calculation failed: {str(e)}",
        )


@router.post("/reset", response_model=TariffConfig)
def reset_tariff_configuration(
    profile: str = Query("commercial", description="Profile to reset to: 'commercial', 'domestic', or 'custom'")
):
    """Reset tariff configuration to initial default editable ranges."""
    try:
        return tariff_service.reset_to_defaults(profile)
    except Exception as e:
        logger.error("Error resetting tariff configuration: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset tariff configuration: {str(e)}",
        )
