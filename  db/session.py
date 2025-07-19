# db/session.py

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

def get_db() -> AsyncIOMotorCollection:
    return db["facebook_insights"]  # ✔ Must be a collection, not the whole DB


