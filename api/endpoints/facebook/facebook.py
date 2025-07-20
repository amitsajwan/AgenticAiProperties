import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase # Corrected import for database object

from db.session import get_db
from services.social_media.facebook_manager import create_facebook_post, PostStatus
from services.social_media.token_service import FacebookTokenService, get_token_service # [NEW] Import token service

logger = logging.getLogger(__name__)
router = APIRouter()

# --------------------------
# Facebook Post Request DTO
# --------------------------
class FacebookPostRequest(BaseModel):
    agent_id: str
    caption: str
    images: List[str] = []
    scheduled_time: Optional[str] = None

# -----------------------
# Create Facebook Post
# -----------------------


@router.post("/posts")
async def create_new_facebook_post(
    post_data: FacebookPostRequest,
    db = Depends(get_db)
):
    """
    Handles the creation and publishing of a Facebook post.
    """
    logger.info(f"Received request to create Facebook post for agent: {post_data.agent_id}")
    try:
        post_result = await create_facebook_post(
            agent_id=post_data.agent_id,
            caption=post_data.caption,
            images=post_data.images,
            db=db
        )
        logger.info(f"Facebook post result: {post_result}")

        if post_result and post_result.status == PostStatus.PUBLISHED:
            # 🧠 NEW: trigger site generation
            from services.website_builder_v2 import WebsiteBuilderV2
            builder = WebsiteBuilderV2(post_data.agent_id, db)
            await builder.generate_site()

            return {
                "status": "success",
                "message": "Post published successfully!",
                "data": post_result
            }

        else:
            # Ensure post_result is a dict before trying to get "message"
            detail_message = post_result.error if isinstance(post_result, BaseModel) and post_result.error else "Unknown error during Facebook post."
            raise HTTPException(status_code=500, detail=detail_message)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error publishing Facebook post for agent {post_data.agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to publish post to Facebook: {e}")


# ------------------------------
# Facebook Token & Page Checker
# ------------------------------
# [MODIFIED] - Renamed endpoint and updated logic to use FacebookTokenService
@router.get("/status/check/{agent_id}")
async def get_facebook_status(
    agent_id: str,
    token_service: FacebookTokenService = Depends(get_token_service) # [MODIFIED] Use get_token_service dependency
):
    logger.info(f"Checking Facebook status for agent: {agent_id}")
    
    access_token_status = 'missing'
    permissions_ok = False

    try:
        # Attempt to get a valid user token (this implicitly checks for token existence and expiry)
        await token_service.get_valid_token(agent_id)
        access_token_status = 'valid'
        logger.info(f"Agent {agent_id} has a valid user access token.")
        
        # If user token is valid, check page permissions
        permissions_ok = await token_service.validate_permissions(agent_id)
        if permissions_ok:
            logger.info(f"Agent {agent_id} has required Facebook permissions.")
        else:
            logger.warning(f"Agent {agent_id} is missing required Facebook permissions.")

        # Additionally, check if page_id and page_access_token are present in the record
        try:
            await token_service.get_page_token_for_agent(agent_id)
            # If get_page_token_for_agent succeeds, it means page_id and page_access_token are present
            logger.info(f"Agent {agent_id} has Facebook page credentials.")
        except HTTPException as e:
            if e.status_code == 404 and "Facebook page ID or page access token not found" in e.detail:
                logger.warning(f"Agent {agent_id} does not have complete Facebook page credentials.")
                # If page credentials are not found, overall status should reflect it
                access_token_status = 'missing' 
            else:
                raise # Re-raise other HTTP exceptions
        except Exception as e:
            logger.error(f"Error checking page credentials for {agent_id}: {e}", exc_info=True)
            access_token_status = 'missing' # Treat unexpected errors as missing credentials
            
    except HTTPException as e:
        if e.status_code == 404:
            logger.warning(f"No Facebook user token found for agent {agent_id}.")
            access_token_status = 'missing'
        elif e.status_code == 403:
            logger.warning(f"Facebook user token for agent {agent_id} is not active or invalid.")
            access_token_status = 'missing'
        else:
            logger.error(f"HTTPException during Facebook status check for {agent_id}: {e.detail}", exc_info=True)
            raise # Re-raise other HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error during Facebook status check for {agent_id}: {e}", exc_info=True)
        access_token_status = 'missing' # Treat unexpected errors as missing credentials

    return {
        "access_token_status": access_token_status,
        "permissions_ok": permissions_ok
    }


# ---------------------
# Insert Test Facebook DB Data
# ---------------------
@router.post("/status/test-insert")
async def insert_facebook_test_data(
    db: AsyncIOMotorDatabase = Depends(get_db) # [MODIFIED] Use AsyncIOMotorDatabase
):
    # This endpoint is for testing purposes, not part of the main flow
    # It inserts a dummy record directly into 'facebook_tokens' for 'test_001'
    from services.social_media.token_service import FacebookTokenService
    token_service = FacebookTokenService(db)

    sample_token_record = {
        "_id": "test_001",
        "access_token": await token_service.encrypt_token("dummy_user_token_123"),
        "expires_at": datetime.datetime.utcnow() + datetime.timedelta(days=60),
        "status": "active",
        "scopes": ["pages_show_list", "pages_read_engagement", "pages_manage_posts"],
        "last_refreshed": datetime.datetime.utcnow(),
        "user_id": "dummy_user_id_123",
        "page_id": "699986296533656", # Use your actual test page ID here
        "page_access_token": await token_service.encrypt_token("dummy_page_token_456"),
        "page_name": "Test Page"
    }
    
    # Use update_one with upsert=True to create or replace the document
    result = await db.facebook_tokens.update_one(
        {"_id": sample_token_record["_id"]},
        {"$set": sample_token_record},
        upsert=True
    )
    
    if result.acknowledged:
        logger.info(f"Test Facebook data inserted/updated for agent {sample_token_record['_id']}")
        return {"status": "inserted/updated", "agent_id": sample_token_record["_id"]}
    else:
        logger.error("Failed to insert/update test Facebook data.")
        raise HTTPException(status_code=500, detail="Failed to insert/update test Facebook data")
