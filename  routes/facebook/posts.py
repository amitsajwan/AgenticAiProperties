from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from db.session import get_db
from models.facebook import FacebookPostResponse, PostStatus

logger = logging.getLogger("facebook_posts")
router = APIRouter()

class FacebookPostRequest(BaseModel):
    agent_id: str
    caption: str
    images: List[str] = []
    scheduled_time: Optional[str] = None

@router.post("/posts")
async def create_new_facebook_post(
    post_data: FacebookPostRequest,
    db: AsyncIOMotorCollection = Depends(get_db)
):
    logger.info(f"[FBPost] Create post request for agent {post_data.agent_id}")

    # Simulated Facebook response
    mock_post_id = f"mock_{datetime.utcnow().timestamp()}"
    post_result = FacebookPostResponse(
        post_id=mock_post_id,
        message=post_data.caption,
        url=f"https://facebook.com/{mock_post_id}",
        agent_id=post_data.agent_id,
        status=PostStatus.PUBLISHED,
        ai_generated=True
    )

    doc = {
        "agent_id": post_data.agent_id,
        "caption": post_data.caption,
        "images": post_data.images,
        "post_id": post_result.post_id,
        "url": post_result.url,
        "status": post_result.status,
        "ai_generated": post_result.ai_generated,
        "created_at": datetime.utcnow()
    }

    try:
        await db.insert_one(doc)
        logger.info(f"[FBPost] Saved post {post_result.post_id} to DB")
    except Exception as e:
        logger.error(f"[FBPost] Failed to save post: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to persist Facebook post")

    return {
        "status": "success",
        "message": "Post published successfully!",
        "data": post_result.model_dump()
    }

