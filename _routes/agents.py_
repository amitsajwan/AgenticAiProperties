from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime
import logging
from db.session import get_db

router = APIRouter()
logger = logging.getLogger("agent")

class AgentSettings(BaseModel):
    agentId: str
    name: str
    email: str
    phone: str
    bio: str

@router.get("/agents/{agent_id}/settings")
async def get_agent_settings(
    agent_id: str,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    agent = await db.find_one({ "agentId": agent_id }, { "_id": 0 })
    if not agent:
        logger.warning(f"[Agent] Settings not found for {agent_id}")
        raise HTTPException(status_code=404, detail="Agent settings not found")
    logger.info(f"[Agent] Retrieved settings for {agent_id}")
    return agent

@router.patch("/agents/{agent_id}")
async def update_agent_settings(
    agent_id: str,
    settings: AgentSettings,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    logger.info(f"[Agent] Updating settings for {agent_id}")
    update_payload = settings.dict()
    update_payload["updated_at"] = datetime.utcnow()

    try:
        await db.update_one(
            { "agentId": agent_id },
            { "$set": update_payload },
            upsert=True
        )
        logger.info(f"[Agent] Settings updated for {agent_id}")
        return update_payload
    except Exception as e:
        logger.error(f"[Agent] Failed to update settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update agent settings")

