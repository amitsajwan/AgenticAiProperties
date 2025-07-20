from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import settings

# Initialize MongoDB client and database
# This client and db object will be reused across the application
client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency that provides the full Motor database object.
    This allows any function using this dependency to access any collection
    within the database (e.g., db.collection_name.find_one()).
    """
    return db
