from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from db.session import get_db
import logging

router = APIRouter()
logger = logging.getLogger("facebook_status")

@router.get("/status/agents/{agent_id}")
async def get_facebook_status(
    agent_id: str,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    logger.info(f"[FBStatus] Checking Facebook status for {agent_id}")

    token_record = await db.find_one({ "_id": agent_id }, { "access_token": 1, "permissions_ok": 1 })

    if not token_record:
        return { "access_token_status": "missing", "permissions_ok": False }

    return {
        "access_token_status": "valid",
        "permissions_ok": token_record.get("permissions_ok", True)
    }

