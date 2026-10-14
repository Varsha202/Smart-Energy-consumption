import os
import logging
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.app.config import settings
from backend.app.database import db_manager, DatabaseUnavailableException
from backend.app.models.schemas import (
    EnergyRecordCreate,
    EnergyRecordResponse,
    EnergyListResponse,
    ImportResponse,
    parse_and_normalize_date
)

logger = logging.getLogger("energy_backend.energy_service")


# Canonical column mappings between CSV and Database fields
CSV_TO_DB_MAP = {
    "Date": "date",
    "TNEB_Campus": "tneb_campus",
    "TNEB_New_STP": "tneb_new_stp",
    "Solar": "solar",
    "Diesel": "diesel",
    "Biogas": "biogas",
    "Staff_Quarters": "staff_quarters",
    "Academic_Blocks": "academic_blocks",
    "Hostels": "hostels",
    "Chiller": "chiller",
    "STP": "stp",
    "Total": "total"
}

DB_TO_CSV_MAP = {v: k for k, v in CSV_TO_DB_MAP.items()}


class EnergyService:
    """Handles energy record CRUD, dataset CSV imports, and persistence."""

    def __init__(self):
        self._fallback_cache: Optional[List[Dict[str, Any]]] = None

    def get_collection(self) -> Collection:
        """Helper to get MongoDB energy collection."""
        return db_manager.get_energy_collection()

    def parse_csv_dataframe(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Validate and convert DataFrame rows into normalized dictionary records."""
        valid_records = []
        errors = []

        # Normalize column names (strip whitespace)
        df.columns = [c.strip() for c in df.columns]

        # Check required columns
        missing_cols = [col for col in CSV_TO_DB_MAP.keys() if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns in dataset: {', '.join(missing_cols)}")
            return valid_records, errors

        for idx, row in df.iterrows():
            row_num = idx + 2  # Considering 1-based index and header
            try:
                date_val = parse_and_normalize_date(str(row["Date"]))
                
                # Parse numeric fields safely without silently inventing data
                record_dict = {"date": date_val}
                for csv_col, db_field in CSV_TO_DB_MAP.items():
                    if db_field == "date":
                        continue
                    val = row[csv_col]
                    if pd.isna(val):
                        raise ValueError(f"Missing measurement for column '{csv_col}'")
                    try:
                        record_dict[db_field] = float(val)
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid non-numeric value '{val}' in column '{csv_col}'")

                # Validate or auto-calculate total
                calc_total = (
                    record_dict["staff_quarters"] +
                    record_dict["academic_blocks"] +
                    record_dict["hostels"] +
                    record_dict["chiller"] +
                    record_dict["stp"]
                )
                if record_dict.get("total") is None or record_dict["total"] <= 0:
                    record_dict["total"] = calc_total

                valid_records.append(record_dict)
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        return valid_records, errors

    def import_records_to_db(self, records: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        """
        Upsert energy records into MongoDB using 'date' as unique key.
        Returns: (inserted_count, updated_count, error_messages)
        """
        try:
            collection = self.get_collection()
        except DatabaseUnavailableException as e:
            logger.warning("MongoDB unavailable for import: %s", str(e))
            raise

        inserted = 0
        updated = 0
        errors = []

        for record in records:
            try:
                # Upsert record based on date
                result = collection.update_one(
                    {"date": record["date"]},
                    {"$set": record},
                    upsert=True
                )
                if result.upserted_id is not None:
                    inserted += 1
                elif result.modified_count > 0:
                    updated += 1
                else:
                    # Record already identical
                    pass
            except PyMongoError as pe:
                errors.append(f"Database error on record {record.get('date')}: {str(pe)}")

        return inserted, updated, errors

    def import_from_file_path(self, file_path: Optional[str] = None) -> ImportResponse:
        """Import records from a local CSV file into the database."""
        path_to_read = file_path or settings.DEFAULT_DATASET_PATH
        if not os.path.exists(path_to_read):
            raise FileNotFoundError(f"Dataset file not found at path: {path_to_read}")

        logger.info("Reading dataset from: %s", path_to_read)
        df = pd.read_csv(path_to_read)
        valid_records, parse_errors = self.parse_csv_dataframe(df)

        if not valid_records:
            return ImportResponse(
                message="No valid records could be extracted from dataset.",
                total_rows_processed=len(df),
                imported_count=0,
                updated_count=0,
                skipped_count=len(df),
                errors=parse_errors
            )

        inserted, updated, db_errors = self.import_records_to_db(valid_records)
        all_errors = parse_errors + db_errors
        skipped = len(df) - (inserted + updated)

        return ImportResponse(
            message=f"Import complete: {inserted} inserted, {updated} updated.",
            total_rows_processed=len(df),
            imported_count=inserted,
            updated_count=updated,
            skipped_count=max(0, skipped),
            errors=all_errors
        )

    def load_fallback_dataframe(self) -> pd.DataFrame:
        """Load the standard preprocessed CSV directly as fallback when MongoDB is down or unpopulated."""
        if os.path.exists(settings.DEFAULT_DATASET_PATH):
            df = pd.read_csv(settings.DEFAULT_DATASET_PATH)
            valid_records, _ = self.parse_csv_dataframe(df)
            clean_df = pd.DataFrame(valid_records)
            clean_df["date"] = pd.to_datetime(clean_df["date"])
            clean_df = clean_df.sort_values("date").reset_index(drop=True)
            return clean_df
        return pd.DataFrame()

    def get_all_records_as_df(self) -> pd.DataFrame:
        """
        Fetch all records as a Pandas DataFrame sorted chronologically by date.
        If MongoDB is connected and has records, queries MongoDB.
        If MongoDB is down or empty, gracefully falls back to default CSV dataset.
        """
        try:
            collection = self.get_collection()
            cursor = collection.find({}, {"_id": 0}).sort("date", ASCENDING)
            docs = list(cursor)
            if docs:
                df = pd.DataFrame(docs)
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").reset_index(drop=True)
                return df
        except (DatabaseUnavailableException, PyMongoError) as e:
            logger.info("MongoDB unavailable (%s), using local dataset fallback.", str(e))

        # Local dataset fallback
        return self.load_fallback_dataframe()

    def list_energy_records(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        limit: int = 100
    ) -> EnergyListResponse:
        """Query records with optional date range filter and pagination."""
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        if limit > 500:
            limit = 500

        filter_query: Dict[str, Any] = {}
        date_filter: Dict[str, str] = {}
        if start_date:
            date_filter["$gte"] = parse_and_normalize_date(start_date)
        if end_date:
            date_filter["$lte"] = parse_and_normalize_date(end_date)
        if date_filter:
            filter_query["date"] = date_filter

        records: List[EnergyRecordResponse] = []
        total_records = 0

        try:
            collection = self.get_collection()
            total_records = collection.count_documents(filter_query)
            skip = (page - 1) * limit
            cursor = collection.find(filter_query).sort("date", ASCENDING).skip(skip).limit(limit)

            for doc in cursor:
                doc["_id"] = str(doc.get("_id", ""))
                records.append(EnergyRecordResponse(**doc))

        except (DatabaseUnavailableException, PyMongoError):
            logger.info("Using dataset fallback for list_energy_records")
            df = self.load_fallback_dataframe()
            if not df.empty:
                if start_date:
                    norm_start = parse_and_normalize_date(start_date)
                    df = df[df["date"] >= norm_start]
                if end_date:
                    norm_end = parse_and_normalize_date(end_date)
                    df = df[df["date"] <= norm_end]

                total_records = len(df)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                slice_df = df.iloc[start_idx:end_idx]

                for _, row in slice_df.iterrows():
                    row_dict = row.to_dict()
                    row_dict["date"] = row["date"].strftime("%Y-%m-%d")
                    records.append(EnergyRecordResponse(**row_dict))

        total_pages = (total_records + limit - 1) // limit if total_records > 0 else 1

        return EnergyListResponse(
            total_records=total_records,
            page=page,
            limit=limit,
            total_pages=total_pages,
            start_date=start_date,
            end_date=end_date,
            records=records
        )

    def add_energy_record(self, record_data: EnergyRecordCreate) -> EnergyRecordResponse:
        """Create or update a single validated energy record."""
        doc = record_data.model_dump()
        try:
            collection = self.get_collection()
            result = collection.update_one(
                {"date": doc["date"]},
                {"$set": doc},
                upsert=True
            )
            created_or_updated = collection.find_one({"date": doc["date"]})
            if created_or_updated:
                created_or_updated["_id"] = str(created_or_updated["_id"])
                return EnergyRecordResponse(**created_or_updated)
        except DatabaseUnavailableException:
            raise DatabaseUnavailableException(
                "Cannot add energy record: MongoDB connection is unavailable."
            )
        return EnergyRecordResponse(**doc)


energy_service = EnergyService()
