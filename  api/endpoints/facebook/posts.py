# api/endpoints/facebook/posts.py

import logging
from typing import List, Optional, Dict, Any # Added Dict, Any for robust post_result handling
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from db.session import get_db

from services.social_media.facebook_manager import create_facebook_post, PostStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Define the request model for your Facebook post
# This tells FastAPI exactly what to expect in the JSON body of the request
class FacebookPostRequest(BaseModel):
    agent_id: str
    caption: str
    images: List[str] = [] # List of image URLs/paths
    scheduled_time: Optional[str] = None # Optional: for future scheduling

@router.post("/posts")
async def create_new_facebook_post(
    # FastAPI will automatically parse the request body into this Pydantic model
    post_data: FacebookPostRequest,
    db = Depends(get_db)
):
    """
    Handles the creation and publishing of a Facebook post.
    """
    logger.info(f"Received request to create Facebook post for agent: {post_data.agent_id}")
    try:
        # Call your core Facebook posting logic
        post_result = await create_facebook_post(
            agent_id=post_data.agent_id,
            caption=post_data.caption,
            images=post_data.images,
            db=db
        )
        logger.info(f"Facebook post result: {post_result}")

        # Ensure the response format matches what the frontend expects
        if post_result and post_result.status == PostStatus.PUBLISHED: # <--- CORRECTED LINE

            return {"status": "success", "message": "Post published successfully!", "data": post_result}
        else:
            detail_message = post_result.get("message", "Unknown error during Facebook post.") if isinstance(post_result, dict) else "Unknown error."
            # If create_facebook_post returns a non-success, raise HTTPException
            raise HTTPException(status_code=500, detail=detail_message)

    except HTTPException as e:
        raise e # Re-raise FastAPI HTTPExceptions
    except Exception as e:
        logger.error(f"Error publishing Facebook post for agent {post_data.agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to publish post to Facebook: {e}")

