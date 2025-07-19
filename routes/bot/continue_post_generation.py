from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime
import logging
from uuid import uuid4
from db.session import get_db

router = APIRouter()
logger = logging.getLogger("post_generation")

class ContinuePostRequest(BaseModel):
    session_id: str
    selected_brand: str

class ContinuePostResponse(BaseModel):
    caption: str
    image_path: str

@router.post("/continue-post-generation", response_model=ContinuePostResponse)
async def continue_post_generation(
    request: ContinuePostRequest,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    logger.info(f"[PostGen] Session: {request.session_id} Brand Selected: {request.selected_brand}")

    # Simulated AI output
    caption = f"Experience luxury living with {request.selected_brand}. Schedule a tour today!"
    image_path = f"/static/images/{uuid4()}.jpg"

    post_record = {
        "session_id": request.session_id,
        "selected_brand": request.selected_brand,
        "caption": caption,
        "image_path": image_path,
        "status": "generated",
        "timestamp": datetime.utcnow()
    }

    try:
        await db.insert_one(post_record)
        logger.info(f"[PostGen] Saved post for session {request.session_id}")
    except Exception as e:
        logger.error(f"[PostGen] Failed to save post: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to persist AI post")

    return ContinuePostResponse(caption=caption, image_path=image_path)

