import logging
from fastapi import APIRouter, HTTPException, Body, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any
from datetime import datetime

from db.session import get_db
from models.facebook import FacebookPostResponse
from models.agent import AgentWebsite
from services.ai.post_workflow import generate_agent_logo
from services.website_builder_v2 import WebsiteBuilderV2

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=AgentWebsite)
async def create_or_update_website(
    data: AgentWebsite,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create or overwrite an agent's website record, then regenerate the static site.
    """
    data_dict = data.model_dump(by_alias=True, exclude_none=False)
    data_dict["_id"] = data.agent_id
    # Ensure logo_prompt doesn't accidentally persist in DB
    data_dict.pop("logo_prompt", None)

    # Upsert the agent_website document
    result = await db.agent_websites.update_one(
        {"_id": data.agent_id},
        {"$set": data_dict},
        upsert=True
    )
    if not result.acknowledged:
        raise HTTPException(500, "Failed to insert/update agent website")

    # Fetch the up-to-date record
    updated_doc = await db.agent_websites.find_one({"_id": data.agent_id})
    if not updated_doc:
        raise HTTPException(500, "Failed to retrieve updated agent website data")

    # Regenerate the static site
    try:
        builder = WebsiteBuilderV2(data.agent_id, db)
        await builder.generate_site()
        logger.info(f"[AgentWebsite] Site regenerated after create/update: {data.agent_id}")
    except Exception as e:
        logger.error(f"[AgentWebsite] Site regeneration error for {data.agent_id}: {e}", exc_info=True)

    return AgentWebsite(**updated_doc)


@router.get("/{agent_id}", response_model=AgentWebsite)
async def get_website(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Retrieve the agent's website record.
    """
    record = await db.agent_websites.find_one({"_id": agent_id})
    if not record:
        raise HTTPException(404, "Agent website not found")
    return AgentWebsite(**record)


@router.get("/{agent_id}/settings", response_model=AgentWebsite)
async def get_agent_settings(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Alias of get_website, used by the frontend to fetch branding settings.
    """
    return await get_website(agent_id, db)


@router.patch("/{agent_id}", response_model=AgentWebsite)
async def update_website(
    agent_id: str,
    updates: Dict[str, Any] = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update branding fields (name, description) and optionally trigger AI logo generation.
    Then regenerate the static site.
    """
    logger.info(f"[AgentWebsite] Updating branding for {agent_id}: {updates}")

    existing = await db.agent_websites.find_one({"_id": agent_id})
    if not existing:
        raise HTTPException(404, "Agent website not found")

    # 1) Handle AI-driven logo generation
    if updates.get("logo_prompt"):
        logo_prompt = updates.pop("logo_prompt")
        logger.info(f"[Branding] Generating logo for {agent_id}: '{logo_prompt}'")
        try:
            new_logo_filename = await generate_agent_logo(agent_id, logo_prompt, db)
            updates["logo_url"] = new_logo_filename

            logger.info(f"[Branding] New logo saved: {new_logo_filename}")
        except Exception as e:
            logger.error(f"[Branding] Logo generation failed: {e}", exc_info=True)
            raise HTTPException(500, f"Logo generation failed: {e}")

    # 2) Apply allowed updates
    for key, value in updates.items():
        if key in existing:
            existing[key] = value

    # 3) Handle posts list if provided
    if "posts" in updates and isinstance(updates["posts"], list):
        parsed_posts: List[FacebookPostResponse] = []
        for item in updates["posts"]:
            if isinstance(item, dict):
                parsed_posts.append(FacebookPostResponse(**item))
            else:
                parsed_posts.append(item)
        existing["posts"] = parsed_posts

    # 4) Persist the merged document
    updated_data = AgentWebsite(**existing).model_dump(by_alias=True, exclude_none=False)
    updated_data["_id"] = agent_id
    await db.agent_websites.update_one({"_id": agent_id}, {"$set": updated_data})
    logger.info(f"[AgentWebsite] Branding updated for {agent_id}")

    # 5) Rebuild the static site
    try:
        builder = WebsiteBuilderV2(agent_id, db)
        await builder.generate_site()
        logger.info(f"[AgentWebsite] Site regenerated after update: {agent_id}")
    except Exception as e:
        logger.error(f"[AgentWebsite] Site regeneration failed: {e}", exc_info=True)
        raise HTTPException(500, f"Website update failed: {e}")

    return AgentWebsite(**updated_data)