import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global database instance
_database: Optional[AsyncIOMotorDatabase] = None
_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None

def initialize_database(database_url: str, db_name: str) -> AsyncIOMotorDatabase:
    """Initialize the database connection."""
    global _database, _client
    
    try:
        _client = motor.motor_asyncio.AsyncIOMotorClient(database_url)
        _database = _client[db_name]
        logger.info(f"Successfully connected to MongoDB database: {db_name}")
        return _database
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance. Initialize if not already done."""
    global _database
    
    if _database is None:
        # Try to initialize with settings
        try:
            from .config import settings
            return initialize_database(settings.DATABASE_URL, settings.MONGO_DB_NAME)
        except ImportError:
            raise RuntimeError("Database not initialized and settings not available")
    
    return _database

async def close_database():
    """Close the database connection."""
    global _client
    if _client:
        _client.close()

# For backward compatibility, create db instance
try:
    from .config import settings
    db = initialize_database(settings.DATABASE_URL, settings.MONGO_DB_NAME)
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    db = None