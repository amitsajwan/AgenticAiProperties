import logging
import os
from typing import List, Optional, Dict, Any
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from core.config import settings
from services.social_media.token_service import FacebookTokenService, get_token_service
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase # Import AsyncIOMotorDatabase
from db.session import get_db # Import get_db

logger = logging.getLogger(__name__)

# --- Re-defining PostStatus and FacebookPostResponse for clarity in this file
#     These should ideally be imported from models/facebook.py
class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"

class FacebookPostResponse(BaseModel):
    post_id: str = Field(..., description="Facebook's unique post identifier")
    message: str = Field(..., max_length=5000, description="Post content text")
    url: Optional[str] = Field(None, description="Permalink to the post on Facebook")
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    status: PostStatus = Field(PostStatus.PUBLISHED)
    engagement: Optional[Dict[str, int]] = Field(None, description="Likes, comments, shares counts")
    error: Optional[str] = Field(None, description="Error details if status=failed")
    scheduled_time: Optional[datetime] = None
    ai_generated: bool = Field(False)
    image_path: Optional[str] = Field(None, description="Path to the generated image for the post") # Ensure this is here

# --- End re-definitions ---


async def create_facebook_post(
    agent_id: str,
    caption: str,
    images: Optional[List[str]] = None, # Expects full URLs or paths that can be resolved
    scheduled_time: Optional[datetime] = None,
    db: AsyncIOMotorDatabase = Depends(get_db) # CRITICAL FIX: Use Depends(get_db)
) -> FacebookPostResponse:
    """
    Creates and publishes a Facebook post for a given agent.
    Can include up to 4 images.
    """
    logger.info(f"Attempting to create Facebook post for agent {agent_id}.")
    token_service = FacebookTokenService(db) # Initialize service with the db

    # 1. Retrieve page access token
    try:
        page_data = await token_service.get_page_token_for_agent(agent_id)
        page_id = page_data.page_id
        page_access_token = page_data.access_token
        logger.info(f"Successfully retrieved page token for page ID: {page_id}")
    except HTTPException as e:
        logger.error(f"Failed to retrieve Facebook credentials for agent {agent_id}: {e.detail}")
        return FacebookPostResponse(
            agent_id=agent_id,
            post_id="N/A",
            message=caption,
            url=None,
            status=PostStatus.FAILED,
            error=f"Failed to retrieve Facebook credentials: {e.detail}",
            ai_generated=True,
            image_path=images[0] if images else None # Pass original image path if available
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving Facebook credentials for agent {agent_id}: {e}", exc_info=True)
        return FacebookPostResponse(
            agent_id=agent_id,
            post_id="N/A",
            message=caption,
            url=None,
            status=PostStatus.FAILED,
            error=f"Unexpected error retrieving Facebook credentials: {str(e)}",
            ai_generated=True,
            image_path=images[0] if images else None
        )

    post_url = f"https://graph.facebook.com/v19.0/{page_id}/photos" # For image posts
    
    # Prepare files for upload
    files = {}
    attached_media_ids = []
    
    # CRITICAL FIX: Get the base directory of the backend project
    # This assumes facebook_manager.py is in services/social_media
    backend_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    generated_images_dir = os.path.join(backend_base_dir, "generated_images")

    # [NEW] Add debug logs for paths
    logger.debug(f"DEBUG: backend_base_dir: {backend_base_dir}")
    logger.debug(f"DEBUG: generated_images_dir: {generated_images_dir}")


    if images:
        for i, img_path_relative in enumerate(images):
            # Assuming img_path_relative is just the filename (e.g., "amit_post_image.png")
            # The AI workflow returns just the filename, so we need to construct the full path.
            image_filename = os.path.basename(img_path_relative) # Ensure it's just the filename
            absolute_image_path = os.path.join(generated_images_dir, image_filename)

            logger.info(f"Attempting to open image from absolute path: {absolute_image_path}")
            if not os.path.exists(absolute_image_path):
                logger.error(f"Image file not found at {absolute_image_path}. This image will not be included.")
                # Continue without this image, or raise an error if images are mandatory
                # Returning a failed post response here as image is critical for this flow
                return FacebookPostResponse(
                    agent_id=agent_id,
                    post_id="N/A",
                    message=caption,
                    url=None,
                    status=PostStatus.FAILED,
                    error=f"Image file not found: {absolute_image_path}",
                    ai_generated=True,
                    image_path=images[0] if images else None
                )
            
            try:
                # Upload image first to get an attached_media ID
                upload_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                upload_params = {
                    "access_token": page_access_token,
                    "published": False # Upload but don't publish yet
                }
                with open(absolute_image_path, "rb") as file_obj:
                    upload_files = {"source": file_obj}
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        upload_resp = await client.post(upload_url, params=upload_params, files=upload_files)
                        upload_resp.raise_for_status()
                        upload_data = upload_resp.json()
                        attached_media_ids.append({"media_fbid": upload_data["id"]})
                        logger.info(f"Image uploaded, media ID: {upload_data['id']}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Facebook image upload failed: {e.response.status_code} - {e.response.text}", exc_info=True)
                # If image upload fails, log and continue without images or mark post as failed
                return FacebookPostResponse(
                    agent_id=agent_id,
                    post_id="N/A",
                    message=caption,
                    url=None,
                    status=PostStatus.FAILED,
                    error=f"Facebook image upload failed: {e.response.text}",
                    ai_generated=True,
                    image_path=images[0] if images else None
                )
            except Exception as e:
                logger.error(f"Error during image upload: {e}", exc_info=True)
                return FacebookPostResponse(
                    agent_id=agent_id,
                    post_id="N/A",
                    message=caption,
                    url=None,
                    status=PostStatus.FAILED,
                    error=f"Error during image upload: {str(e)}",
                    ai_generated=True,
                    image_path=images[0] if images else None
                )
    
    # Prepare post parameters
    post_params = {
        "message": caption,
        "access_token": page_access_token,
    }

    if attached_media_ids:
        post_params["attached_media"] = attached_media_ids
        post_url = f"https://graph.facebook.com/v19.0/{page_id}/feed" # For multi-image posts, use /feed endpoint

    if scheduled_time:
        post_params["scheduled_publish_time"] = int(scheduled_time.timestamp())
        post_params["published"] = False # Must be false for scheduled posts

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Attempting to publish post to Facebook for page ID: {page_id}")
            response = await client.post(post_url, json=post_params) # Use json for attached_media
            response.raise_for_status()
            post_data = response.json()
            logger.info(f"Facebook post successful. Post ID: {post_data.get('id')}")

            # Fetch permalink
            permalink = None
            if post_data.get("id"):
                permalink_url = f"https://graph.facebook.com/v19.0/{post_data['id']}"
                permalink_params = {"fields": "permalink_url", "access_token": page_access_token}
                permalink_resp = await client.get(permalink_url, params=permalink_params)
                permalink_resp.raise_for_status()
                permalink_data = permalink_resp.json()
                permalink = permalink_data.get("permalink_url")
                logger.info(f"Facebook post permalink: {permalink}")

            return FacebookPostResponse(
                agent_id=agent_id,
                post_id=post_data.get("id", "N/A"),
                message=caption,
                url=permalink,
                status=PostStatus.PUBLISHED if not scheduled_time else PostStatus.SCHEDULED,
                ai_generated=True,
                image_path=images[0] if images else None # Store the original relative image path
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"Facebook API error during post creation: {e.response.status_code} - {e.response.text}", exc_info=True)
        return FacebookPostResponse(
            agent_id=agent_id,
            post_id="N/A",
            message=caption,
            url=None,
            status=PostStatus.FAILED,
            error=f"Facebook API error: {e.response.text}",
            ai_generated=True,
            image_path=images[0] if images else None
        )
    except Exception as e:
        logger.error(f"Unexpected error during Facebook post creation: {e}", exc_info=True)
        return FacebookPostResponse(
            agent_id=agent_id,
            post_id="N/A",
            message=caption,
            url=None,
            status=PostStatus.FAILED,
            error=f"Unexpected error: {str(e)}",
            ai_generated=True,
            image_path=images[0] if images else None
        )

# This function is not used in the current flow but might be for fetching existing posts
async def get_facebook_posts(page_id: str, access_token: str) -> List[dict]:
    url = f"https://graph.facebook.com/v19.0/{page_id}/posts"
    params = {"access_token": access_token, "fields": "id,message,created_time,full_picture,permalink_url,shares,comments.summary(true),reactions.summary(true)"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            posts = []
            for item in data.get("data", []):
                posts.append({
                    "id": item.get("id"),
                    "message": item.get("message"),
                    "created_time": item.get("created_time"),
                    "full_picture": item.get("full_picture"),
                    "permalink_url": item.get("permalink_url"),
                    "shares": item.get("shares", {}).get("count", 0),
                    "comments": item.get("comments", {}).get("summary", {}).get("total_count", 0),
                    "likes": item.get("reactions", {}).get("summary", {}).get("total_count", 0),
                })
            return posts
    except httpx.HTTPStatusError as e:
        logger.error(f"Facebook API error fetching posts: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch Facebook posts: {e}", exc_info=True)
        return []
