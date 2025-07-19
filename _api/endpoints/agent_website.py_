from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from db.session import get_db
from datetime import datetime

router = APIRouter()

class AgentWebsite(BaseModel):
    agent_id: str
    name: str
    description: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    cover_image_url: Optional[HttpUrl] = None
    posts: List[str] = []

@router.post("/", response_model=AgentWebsite)
async def create_or_update_website(
    data: AgentWebsite,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    """
    Create or overwrite an agent's website data in MongoDB.
    """
    result = await db.agent_websites.update_one(
        {"agent_id": data.agent_id},
        {"$set": data.dict()},
        upsert=True
    )

    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to insert/update agent website")

    return data


@router.get("/{agent_id}", response_model=AgentWebsite)
async def get_website(
    agent_id: str,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    """
    Retrieve an agent's website data.
    """
    record = await db.agent_websites.find_one({"agent_id": agent_id})
    if not record:
        raise HTTPException(status_code=404, detail="Agent website not found")
    return AgentWebsite(**record)


@router.get("/{agent_id}/settings", response_model=AgentWebsite)
async def get_agent_settings(
    agent_id: str,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    return await get_website(agent_id, db)


@router.patch("/{agent_id}", response_model=AgentWebsite)
async def update_website(
    agent_id: str,
    updates: dict = Body(...),
    db: AsyncIOMotorCollection = Depends(get_db)
):
    """
    Partially update an agent's website.
    """
    existing = await db.agent_websites.find_one({"agent_id": agent_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Agent website not found")

    existing.update(updates)
    await db.agent_websites.update_one(
        {"agent_id": agent_id},
        {"$set": existing}
    )

    return AgentWebsite(**existing)

@router.post("/status/test-insert")
async def insert_facebook_test_data(db: AsyncIOMotorCollection = Depends(get_db)):
    sample = {
        "_id": "test_001",
        "facebook": {
            "tokens": {
                "access_token": "test_token"
            },
            "pages": [
                {"id": "12345", "name": "Test Page"}
            ]
        }
    }
    await db.facebook.insert_one(sample)
    return {"status": "inserted"}

