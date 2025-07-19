import logging
import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from db.session import get_db
# Assuming FacebookPostResponse is defined somewhere, e.g., in models.facebook
# from models.facebook import FacebookPostResponse # No longer directly used in Pydantic model for post_result
from services.ai.post_workflow import post_graph, BrandingPostState
from services.social_media.facebook_manager import create_facebook_post
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

initial_state_store = {}

class BrandSuggestionResponse(BaseModel):
    session_id: str
    brand_suggestions: str

class SelectBrandRequest(BaseModel):
    session_id: str
    selected_brand: str

class ContentGenerationResponse(BaseModel):
    caption: str
    image_path: str
    post_result: Optional[Dict[str, Any]] = None # Changed to Dict[str, Any] to accept a dictionary

@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for client: {client_id}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from {client_id}: {data}")
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for client: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}", exc_info=True)


@router.post("/generate-branding", response_model=BrandSuggestionResponse)
async def generate_branding(
    agent_id: str = Body(..., description="Agent identifier"),
    prompt:   str = Body(..., description="Free-text prompt for AI"),
    db = Depends(get_db)
):
    logger.info(f"AI→branding request for agent_id={agent_id}, prompt={prompt}")

    session_id = str(uuid.uuid4())

    initial_state: BrandingPostState = {
        "user_input": prompt,
        "client_id": agent_id,
        "db": db,
        "brand_suggestions": None,
        "selected_brand": None,
        "visual_prompts": None,
        "image_path": None,
        "location": None,
        "price": None,
        "bedrooms": None,
        "features": [],
        "base_post": None,
        "missing_info": [],
        "post_result": None,
        "websocket": None
    }

    try:
        final_state = await post_graph.ainvoke(initial_state)
        brand_suggestions = final_state.get("brand_suggestions")

        if not brand_suggestions:
            raise HTTPException(status_code=500, detail="Failed to generate brand suggestions from AI.")

        initial_state_store[session_id] = final_state
        logger.info(f"Generated brand suggestions for session {session_id}: {brand_suggestions[:100]}...")
        return BrandSuggestionResponse(session_id=session_id, brand_suggestions=brand_suggestions)

    except Exception as e:
        logger.error(f"AI branding generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI workflow error during branding generation: {e}")


@router.post("/continue-post-generation", response_model=ContentGenerationResponse)
async def continue_post_generation(
    request: SelectBrandRequest,
    db = Depends(get_db)
):
    session_id = request.session_id
    selected_brand = request.selected_brand

    logger.info(f"AI→continue post generation for session {session_id} with selected brand: {selected_brand[:50]}...")

    current_state: Optional[BrandingPostState] = initial_state_store.pop(session_id, None)
    if not current_state:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please restart the process.")

    current_state["selected_brand"] = selected_brand
    current_state["db"] = db

    try:
        final_state = await post_graph.ainvoke(current_state)

        caption = final_state.get("base_post")
        image_path = final_state.get("image_path")
        
        # FIX: Convert FacebookPostResponse object to a dictionary
        raw_post_result = final_state.get("post_result")
        processed_post_result = None
        if raw_post_result:
            # Assuming FacebookPostResponse has a .model_dump() or .dict() method
            # If it's just a simple dataclass, you might need dataclasses.asdict()
            if hasattr(raw_post_result, 'model_dump'):
                processed_post_result = raw_post_result.model_dump()
            elif hasattr(raw_post_result, 'dict'): # For Pydantic v1 or older versions
                processed_post_result = raw_post_result.dict()
            elif isinstance(raw_post_result, dict): # If it's already a dict
                processed_post_result = raw_post_result
            else:
                # Fallback if it's some other object, might need more specific handling
                processed_post_result = str(raw_post_result) # Convert to string if it's complex
                logger.warning(f"Unexpected type for post_result: {type(raw_post_result)}. Converted to string.")
        
        if not caption or not image_path:
            raise HTTPException(status_code=500, detail="Failed to generate post content from AI.")

        logger.info(f"Generated full post for session {session_id}. Caption: {caption[:100]}...")
        return ContentGenerationResponse(
            caption=caption,
            image_path=image_path,
            post_result=processed_post_result # Pass the processed dictionary here
        )

    except Exception as e:
        logger.error(f"AI post generation failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI workflow error during post generation: {e}")

