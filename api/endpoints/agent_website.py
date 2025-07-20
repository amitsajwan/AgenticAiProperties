import logging
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from db.session import get_db
from datetime import datetime
from models.facebook import FacebookPostResponse 
from services.ai.post_workflow import generate_agent_logo 
from services.website_builder_v2 import WebsiteBuilderV2 
from models.agent import AgentWebsite

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=AgentWebsite)
async def create_or_update_website(
    data: AgentWebsite,
    db: AsyncIOMotorDatabase = Depends(get_db) 
):
    """
    Create or overwrite an agent's website data in MongoDB.
    """
    data_dict = data.model_dump(by_alias=True, exclude_none=False) 
    data_dict["_id"] = data_dict["agent_id"] 

    if "logo_prompt" in data_dict:
        del data_dict["logo_prompt"]

    result = await db.agent_websites.update_one(
        {"_id": data.agent_id}, 
        {"$set": data_dict},
        upsert=True
    )

    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to insert/update agent website")

    updated_doc = await db.agent_websites.find_one({"_id": data.agent_id})
    if not updated_doc:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated agent website data")

    try:
        builder = WebsiteBuilderV2(data.agent_id, db)
        await builder.generate_site()
        logger.info(f"Agent website for {data.agent_id} regenerated after creation/update.")
    except Exception as e:
        logger.error(f"Failed to regenerate site for {data.agent_id} after creation/update: {e}", exc_info=True)

    return AgentWebsite(**updated_doc)


@router.get("/{agent_id}", response_model=AgentWebsite)
async def get_website(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db) 
):
    """
    Retrieve an agent's website data.
    """
    record = await db.agent_websites.find_one({"_id": agent_id}) 
    if not record:
        raise HTTPException(status_code=404, detail="Agent website not found")
    return AgentWebsite(**record)

@router.get("/{agent_id}/settings", response_model=AgentWebsite)
async def get_agent_settings(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db) 
):
    return await get_website(agent_id, db)

@router.patch("/{agent_id}", response_model=AgentWebsite)
async def update_website(
    agent_id: str,
    updates: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db) 
):
    """Update agent branding with AI-generated logo"""
    logger.info(f"Updating branding for {agent_id}: {updates}")
    existing = await db.agent_websites.find_one({"_id": agent_id}) 
    if not existing:
        raise HTTPException(status_code=404, detail="Agent website not found")

    # Handle logo generation
    if "logo_prompt" in updates and updates["logo_prompt"]:
        logo_prompt = updates["logo_prompt"]
        logger.info(f"Generating new logo for {agent_id}: '{logo_prompt}'")
        
        try:
            logo_url = await generate_agent_logo(agent_id, logo_prompt, db)
            updates["logo_url"] = logo_url
            logger.info(f"Logo generated: {logo_url}")
        except Exception as e:
            logger.error(f"Logo generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"Logo generation failed: {str(e)}"
            )
    
    # Remove prompt field after processing
    if "logo_prompt" in updates:
        del updates["logo_prompt"]
    
    # Apply updates
    for key, value in updates.items():
        if key in existing:
            existing[key] = value
    
    # Update posts if provided
    if 'posts' in updates and updates['posts'] is not None:
        updated_posts = []
        for post_data in updates['posts']:
            if isinstance(post_data, dict):
                updated_posts.append(FacebookPostResponse(**post_data))
            else:
                updated_posts.append(post_data) 
        existing['posts'] = updated_posts

    # Save to database
    updated_data = AgentWebsite(**existing).model_dump(by_alias=True, exclude_none=False)
    updated_data["_id"] = agent_id
    
    await db.agent_websites.update_one(
        {"_id": agent_id},
        {"$set": updated_data}
    )
    logger.info(f"Branding updated for {agent_id}")

    # Regenerate website
    try:
        builder = WebsiteBuilderV2(agent_id, db)
        await builder.generate_site()
        logger.info(f"Website regenerated for {agent_id}")
    except Exception as e:
        logger.error(f"Website regeneration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Website update failed: {str(e)}"
        )
    
    return AgentWebsite(**updated_data)