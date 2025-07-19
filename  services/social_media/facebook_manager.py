# services/social_media/facebook_manager.py

import os
import httpx
import logging
import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from fastapi import HTTPException, Depends
from services.social_media.token_service import FacebookTokenService
from db.session import get_db

logger = logging.getLogger(__name__)

# Corrected PostStatus Enum
class PostStatus(str, Enum):
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"
    PENDING = "pending" # For internal workflow status

# Define FacebookPostResponse Model
class FacebookPostResponse(BaseModel):
    post_id: str
    message: str
    url: Optional[str] = None
    agent_id: str
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: Optional[datetime.datetime] = None
    status: PostStatus = PostStatus.PENDING
    engagement: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    scheduled_time: Optional[datetime.datetime] = None
    ai_generated: bool = False


async def create_facebook_post(
    agent_id: str,
    caption: str,
    images: List[str],
    db = Depends(get_db),
    scheduled_time: Optional[datetime.datetime] = None
) -> FacebookPostResponse:
    logger.info(f"Attempting to create Facebook post for agent {agent_id}.")

    token_service = FacebookTokenService(db)
    
    page_id = None
    access_token = None

    try:
        page_data = await token_service.get_page_token_for_agent(agent_id)
        page_id = page_data.page_id
        access_token = page_data.access_token
        logger.info(f"Successfully retrieved page token for page ID: {page_id}")

    except HTTPException as e:
        logger.error(f"Failed to retrieve Facebook credentials for agent {agent_id}: {e.detail}", exc_info=True)
        return FacebookPostResponse(
            post_id="N/A",
            message=caption,
            agent_id=agent_id,
            status=PostStatus.FAILED,
            error=f"Failed to retrieve Facebook credentials: {e.detail}"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving Facebook credentials for agent {agent_id}: {e}", exc_info=True)
        return FacebookPostResponse(
            post_id="N/A",
            message=caption,
            agent_id=agent_id,
            status=PostStatus.FAILED,
            error=f"Unexpected error retrieving Facebook credentials: {e}"
        )

    base_url = f"https://graph.facebook.com/{os.getenv('FB_API_VERSION', 'v19.0')}"

    # 1. Upload images (if any)
    media_ids = []
    for image_path in images:
        absolute_image_path = os.path.abspath(image_path)
        logger.info(f"Attempting to open image from absolute path: {absolute_image_path}")

        try:
            with open(absolute_image_path, "rb") as file_obj:
                files = {"source": file_obj}
                # Upload to /photos endpoint with published=false to get a media_id
                upload_url = f"{base_url}/{page_id}/photos?access_token={access_token}&published=false"
                async with httpx.AsyncClient() as client:
                    upload_response = await client.post(upload_url, files=files)
                    upload_response.raise_for_status()
                    media_id = upload_response.json().get("id")
                    if media_id:
                        media_ids.append(media_id)
                        logger.info(f"Image uploaded with media ID: {media_id}")
                    else:
                        logger.error(f"Image upload failed, no media ID: {upload_response.text}")
                        return FacebookPostResponse(
                            post_id="N/A",
                            message=caption,
                            agent_id=agent_id,
                            status=PostStatus.FAILED,
                            error=f"Image upload failed: {upload_response.text}"
                        )
        except FileNotFoundError:
            logger.error(f"Image file not found at {absolute_image_path}. This image will not be included.", exc_info=True)
            return FacebookPostResponse(
                post_id="N/A",
                message=caption,
                agent_id=agent_id,
                status=PostStatus.FAILED,
                error=f"Image file not found: {absolute_image_path}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Error uploading image to Facebook: {e.response.text}", exc_info=True)
            return FacebookPostResponse(
                post_id="N/A",
                message=caption,
                agent_id=agent_id,
                status=PostStatus.FAILED,
                error=f"Facebook API Error (Image Upload): {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during image upload: {e}", exc_info=True)
            return FacebookPostResponse(
                post_id="N/A",
                message=caption,
                agent_id=agent_id,
                status=PostStatus.FAILED,
                error=f"Unexpected error during image upload: {e}"
            )

    # 2. Create the post
    # For publishing with attached media, always use the /feed endpoint.
    post_url = f"{base_url}/{page_id}/feed"
    post_data = {"message": caption, "access_token": access_token}

    if media_ids:
        # Attach media_ids for the post. For single image, it's just one item.
        # For multiple, Facebook treats them as a multi-photo post if the page supports it.
        attached_media_list = []
        for i, media_id in enumerate(media_ids):
            attached_media_list.append({"media_fbid": media_id})
        
        # When sending multiple attached_media, it should be an array of objects
        # or use attached_media[0], attached_media[1] for form data.
        # httpx typically handles list of dicts for `json` parameter or `data` for form fields.
        # For `x-www-form-urlencoded` or `multipart/form-data`, you'd typically send:
        # attached_media[0][media_fbid]=MEDIA_ID_1&attached_media[1][media_fbid]=MEDIA_ID_2
        # Let's ensure it's sent as a form field.
        for i, media_obj in enumerate(attached_media_list):
            post_data[f"attached_media[{i}]"] = media_obj # This should correctly format for form data

    if scheduled_time:
        post_data["scheduled_publish_time"] = int(scheduled_time.timestamp())
        post_data["published"] = False
        post_status = PostStatus.SCHEDULED
    else:
        post_status = PostStatus.PUBLISHED

    try:
        async with httpx.AsyncClient() as client:
            # Send as data (form-urlencoded or multipart)
            final_post_response = await client.post(post_url, data=post_data)
            final_post_response.raise_for_status()
            post_response_data = final_post_response.json()
            post_id = post_response_data.get("id") or post_response_data.get("post_id")

            if post_id:
                post_url_fb = f"https://facebook.com/{post_id}"
                logger.info(f"Post successful! Post ID: {post_id}, URL: {post_url_fb}")
                return FacebookPostResponse(
                    post_id=post_id,
                    message=caption,
                    url=post_url_fb,
                    agent_id=agent_id,
                    status=post_status,
                    ai_generated=True
                )
            else:
                logger.error(f"Post successful but no post ID returned: {final_post_response.text}")
                return FacebookPostResponse(
                    post_id="N/A",
                    message=caption,
                    agent_id=agent_id,
                    status=PostStatus.FAILED,
                    error=f"Post successful but no post ID: {final_post_response.text}"
                )

    except httpx.HTTPStatusError as e:
        logger.error(f"Error creating Facebook post: {e.response.text}", exc_info=True)
        return FacebookPostResponse(
            post_id="N/A",
            message=caption,
            agent_id=agent_id,
            status=PostStatus.FAILED,
            error=f"Facebook API Error (Post Creation): {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during Facebook post creation: {e}", exc_info=True)
        return FacebookPostResponse(
            post_id="N/A",
            message=caption,
            agent_id=agent_id,
            status=PostStatus.FAILED,
            error=f"Unexpected error during Facebook post creation: {e}"
        )

