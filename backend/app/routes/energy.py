import io
import os
import logging
from typing import Optional
from fastapi import APIRouter, Query, UploadFile, File, HTTPException, status
import pandas as pd

from ..config import settings
from ..database import DatabaseUnavailableException
from ..models.schemas import (
    EnergyListResponse,
    EnergyRecordCreate,
    EnergyRecordResponse,
    ImportResponse
)
from ..services.energy_service import energy_service

logger = logging.getLogger("energy_backend.routes.energy")
router = APIRouter(prefix="/api/energy", tags=["Energy Data"])


@router.get("", response_model=EnergyListResponse)
def list_energy_records(
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD or DD.MM.YYYY)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD or DD.MM.YYYY)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(100, ge=1, le=500, description="Records per page (max 500)")
):
    """Retrieve energy records with optional date filtering and pagination."""
    try:
        return energy_service.list_energy_records(
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error("Error retrieving energy records: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch energy records: {str(e)}"
        )


@router.post("", response_model=EnergyRecordResponse, status_code=status.HTTP_201_CREATED)
def create_energy_record(record: EnergyRecordCreate):
    """Create or update a validated single energy record."""
    try:
        return energy_service.add_energy_record(record)
    except DatabaseUnavailableException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database is unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error("Error creating energy record: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create energy record: {str(e)}"
        )


@router.post("/import", response_model=ImportResponse)
async def import_energy_data(
    file: Optional[UploadFile] = File(None),
    use_default_dataset: bool = Query(False, description="Import directly from designated repository CSV")
):
    """
    Import energy data into MongoDB with automatic deduplication (upsert by Date).
    Supports uploading a CSV/XLSX file or importing the designated preprocessed dataset.
    """
    try:
        # If a file was uploaded
        if file is not None and file.filename:
            content = await file.read()
            filename = file.filename.lower()
            
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file format. Please upload a .csv or .xlsx file."
                )

            valid_records, parse_errors = energy_service.parse_csv_dataframe(df)
            if not valid_records:
                return ImportResponse(
                    message="No valid records could be extracted from uploaded file.",
                    total_rows_processed=len(df),
                    imported_count=0,
                    updated_count=0,
                    skipped_count=len(df),
                    errors=parse_errors
                )

            inserted, updated, db_errors = energy_service.import_records_to_db(valid_records)
            skipped = len(df) - (inserted + updated)

            return ImportResponse(
                message=f"File '{file.filename}' processed successfully.",
                total_rows_processed=len(df),
                imported_count=inserted,
                updated_count=updated,
                skipped_count=max(0, skipped),
                errors=parse_errors + db_errors
            )

        # Default dataset file import
        if use_default_dataset or file is None:
            return energy_service.import_from_file_path(settings.DEFAULT_DATASET_PATH)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided. Specify a file upload or set use_default_dataset=true."
        )

    except DatabaseUnavailableException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database is unavailable for import: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during energy import: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
