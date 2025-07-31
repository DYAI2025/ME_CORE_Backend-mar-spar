import motor.motor_asyncio
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create MongoDB client with connection string from environment
try:
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.DATABASE_URL)
    db = client[settings.MONGO_DB_NAME]
    logger.info(f"Successfully connected to MongoDB database: {settings.MONGO_DB_NAME}")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise