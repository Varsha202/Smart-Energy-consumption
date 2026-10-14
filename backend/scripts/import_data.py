import sys
import os
import argparse
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.config import settings
from backend.app.database import db_manager, DatabaseUnavailableException
from backend.app.services.energy_service import energy_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("import_data")


def main():
    parser = argparse.ArgumentParser(
        description="Import energy dataset CSV into MongoDB for Smart Campus Energy Analytics."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=settings.DEFAULT_DATASET_PATH,
        help="Path to CSV dataset file (defaults to data/preprocessed_energy.csv)"
    )
    args = parser.parse_args()

    file_path = args.file
    logger.info("Connecting to MongoDB at '%s'...", settings.MONGODB_URI)
    db_manager.connect()

    if not db_manager.ping():
        logger.error(
            "ERROR: Cannot connect to MongoDB at %s. Please verify that the MongoDB service is running.",
            settings.MONGODB_URI
        )
        sys.exit(1)

    logger.info("Importing dataset from '%s' into collection '%s'...", file_path, settings.ENERGY_COLLECTION)
    try:
        response = energy_service.import_from_file_path(file_path)
        logger.info("=== Import Results ===")
        logger.info("Status: %s", response.message)
        logger.info("Rows processed: %d", response.total_rows_processed)
        logger.info("Records inserted: %d", response.imported_count)
        logger.info("Records updated: %d", response.updated_count)
        logger.info("Rows skipped: %d", response.skipped_count)
        if response.errors:
            logger.warning("Warnings/Errors encountered (%d):", len(response.errors))
            for err in response.errors[:10]:
                logger.warning("  - %s", err)
            if len(response.errors) > 10:
                logger.warning("  ... and %d more errors.", len(response.errors) - 10)
    except DatabaseUnavailableException as e:
        logger.error("Database unavailable error during import: %s", str(e))
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to import dataset: %s", str(e))
        sys.exit(1)
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
