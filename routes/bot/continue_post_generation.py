import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4

from db.session import get_db
from services.generation.branding_to_post_graph import post_graph
from core.models.agent_post import AgentPost

logger = logging.getLogger(__name__)
router = APIRouter()


class ContinuePostRequest(BaseModel):
    session_id: str
    selected_brand: str

class ContinuePostResponse(BaseModel):
    caption: str
    image_path: Optional[str]


@router.post("/continue-post-generation", response_model=ContinuePostResponse)
async def continue_post_generation(request: ContinuePostRequest, db=Depends(get_db)):
    """
    Continues the branding + post creation LangGraph chain after brand is selected.
    """
    try:
        logger.info(f"[PostGen] Continuing session: {request.session_id} with brand: {request.selected_brand}")

        # Fetch the existing session state from DB
        session_doc = await db.posts.find_one({"session_id": request.session_id})
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")

        # Rehydrate state
        state = session_doc.get("state", {})
        state["selected_brand"] = request.selected_brand
        state["client_id"] = session_doc.get("agent_id")
        state["db"] = db

        # Run the LangGraph
        async for output in post_graph.stream(state):
            state.update(output)

        caption = state.get("base_post", "")
        image_path = state.get("image_path")

        # Save the updated post with final caption and image
        post_record = {
            "session_id": request.session_id,
            "agent_id": session_doc.get("agent_id"),
            "caption": caption,
            "image_path": image_path,
            "state": state
        }
        await db.posts.insert_one(post_record)
        logger.info(f"[PostGen] Saved post for session {request.session_id}")

        # Optional: Save branding metadata to agent_website
        try:
            await db.agent_websites.update_one(
                {"agent_id": session_doc.get("agent_id")},
                {"$set": {
                    "selected_brand": request.selected_brand,
                    "brand_suggestions": session_doc.get("state", {}).get("brand_suggestions"),
                    "logo_url": image_path,
                    "branding_complete": True
                }},
                upsert=True
            )
            logger.info(f"[PostGen] Updated branding for agent {session_doc.get('agent_id')}")
        except Exception as e:
            logger.error(f"[PostGen] Failed to update agent_website: {str(e)}")

        return ContinuePostResponse(caption=caption, image_path=image_path)

    except Exception as e:
        logger.exception(f"[PostGen] Error during continue_post_generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Post generation failed")
