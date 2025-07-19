# api/endpoints/facebook/status.py

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from db.session import get_db

router = APIRouter()

@router.get("/status/agents/{agent_id}")
async def get_facebook_status(
    agent_id: str,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    doc = await db.facebook.find_one({"_id": agent_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Agent Facebook data not found")

    facebook_data = doc.get("facebook", {})

    return {
        "token_valid": bool(facebook_data.get("tokens")),
        "page_connected": bool(facebook_data.get("pages"))
    }

@router.post("/status/test-insert")
async def insert_facebook_test_data(
    db: AsyncIOMotorCollection = Depends(get_db)
):
    sample = {
        "_id": "test_001",
        "facebook": {
            "tokens": {"access_token": "test_token"},
            "pages": [{"id": "12345", "name": "Test Page"}]
        }
    }
    await db.facebook.insert_one(sample)
    return {"status": "inserted"}


