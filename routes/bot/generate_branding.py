from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from db.session import get_db

router = APIRouter()
logger = logging.getLogger("branding")

class BrandingRequest(BaseModel):
    agent_id: str
    prompt: str

class BrandingResponse(BaseModel):
    session_id: str
    brand_suggestions: str

@router.post("/generate-branding", response_model=BrandingResponse)
async def generate_branding(
    request: BrandingRequest = Body(...),
    db: AsyncIOMotorCollection = Depends(get_db)
):
    logger.info(f"[Branding] Agent: {request.agent_id} Prompt: {request.prompt}")
    

    sample_suggestions = [
        "Urban Nest Realty",
        "Skyline Luxe Properties",
        "Elevate Estates",
        "Downtown Dwellers Group",
        "Panorama Properties Co."
    ]
    formatted = "\n".join(sample_suggestions)
    session_id = str(uuid4())

    branding_record = {
        "session_id": session_id,
        "agent_id": request.agent_id,
        "prompt": request.prompt,
        "brand_suggestions": sample_suggestions,
        "created_at": datetime.utcnow()
    }

    try:
        await db.insert_one(branding_record)
        logger.info(f"[Branding] Session saved: {session_id}")
    except Exception as e:
        logger.error(f"[Branding] Failed to save session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to persist branding session")

    return BrandingResponse(session_id=session_id, brand_suggestions=formatted)

