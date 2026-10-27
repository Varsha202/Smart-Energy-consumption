import logging
from typing import Optional, Generator
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
from .config import settings

logger = logging.getLogger("energy_backend.database")


class DatabaseUnavailableException(Exception):
    """Raised when MongoDB is unreachable or operations fail due to database downtime."""
    pass


class MongoDBManager:
    """Manages the PyMongo client lifecycle, connection status, and indexing."""
    
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def connect(self) -> None:
        """Initialize MongoDB client with safe timeout parameters."""
        try:
            logger.info("Initializing MongoDB connection to %s", settings.MONGODB_URI.split("@")[-1])
            self._client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=3000
            )
            self._db = self._client[settings.DATABASE_NAME]
            # Try a lightweight ping to verify connectivity immediately
            self.ping()
            self._ensure_indexes()
            logger.info("Successfully connected to MongoDB database '%s'", settings.DATABASE_NAME)
        except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as exc:
            logger.warning("MongoDB is currently unreachable: %s", str(exc))
            # We do not crash the application so health checks can report the status gracefully

    def _ensure_indexes(self) -> None:
        """Create unique indexes to prevent accidental duplicate entries."""
        if self._db is not None:
            try:
                collection = self._db[settings.ENERGY_COLLECTION]
                collection.create_index([("date", ASCENDING)], unique=True)
                logger.info("Ensured unique index on '%s.date'", settings.ENERGY_COLLECTION)
            except Exception as e:
                logger.warning("Could not create index on energy collection: %s", str(e))

            try:
                notif_collection = self._db[settings.NOTIFICATION_COLLECTION]
                notif_collection.create_index([("dedup_key", ASCENDING)], unique=True)
                notif_collection.create_index([("is_read", ASCENDING)])
                notif_collection.create_index([("created_at", ASCENDING)])
                logger.info("Ensured indexes on '%s'", settings.NOTIFICATION_COLLECTION)
            except Exception as e:
                logger.warning("Could not create index on notification collection: %s", str(e))

    def ping(self) -> bool:
        """Check if the database server is responsive."""
        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError):
            return False

    def get_database(self) -> Database:
        """Retrieve the database instance or raise DatabaseUnavailableException if down."""
        if self._client is None:
            self.connect()

        if not self.ping():
            raise DatabaseUnavailableException(
                "MongoDB service is unavailable or unreachable. "
                "Please verify that MongoDB is running and MONGODB_URI is correctly configured."
            )
        return self._client[settings.DATABASE_NAME]

    def get_energy_collection(self) -> Collection:
        """Retrieve the energy collection from the active database."""
        db = self.get_database()
        return db[settings.ENERGY_COLLECTION]

    def get_notification_collection(self) -> Collection:
        """Retrieve the notifications collection from the active database."""
        db = self.get_database()
        return db[settings.NOTIFICATION_COLLECTION]

    def close(self) -> None:
        """Safely close client connections."""
        if self._client:
            logger.info("Closing MongoDB client connection.")
            self._client.close()
            self._client = None
            self._db = None


# Global singleton instance
db_manager = MongoDBManager()


def get_db() -> Generator[Database, None, None]:
    """FastAPI dependency for accessing database with proper error trapping."""
    try:
        db = db_manager.get_database()
        yield db
    except DatabaseUnavailableException:
        raise
