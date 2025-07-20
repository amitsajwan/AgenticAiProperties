import logging
import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, Body, Depends, HTTPException, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.session import get_db
from models.facebook import FacebookPostResponse # Assuming this model is defined
from services.ai.post_workflow import post_graph, BrandingPostState # Assuming these are defined
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Existing Models (adjust based on your actual models) ---
class BrandSuggestionResponse(BaseModel):
    session_id: str
    brand_suggestions: str

class SelectBrandRequest(BaseModel):
    session_id: str
    selected_brand: str

class ContentGenerationResponse(BaseModel):
    caption: str
    image_path: str
    post_result: Optional[FacebookPostResponse] = None
# --- End Existing Models ---

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
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    logger.info(f"AI->branding request for agent_id={agent_id}, prompt={prompt}")
    session_id = str(uuid.uuid4())

    # Initial state for the AI workflow graph
    initial_state: BrandingPostState = {
        "user_input": prompt,
        "client_id": agent_id,
        "db": db, # The 'db' object is included here for the AI graph's internal use
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
        # Invoke the AI graph to generate brand suggestions
        final_state = await post_graph.ainvoke(initial_state)
        brand_suggestions = final_state.get("brand_suggestions")

        if not brand_suggestions:
            raise HTTPException(status_code=500, detail="Failed to generate brand suggestions from AI.")
        
        # CRITICAL FIX: Convert FacebookPostResponse within final_state to a dictionary for BSON serialization
        serializable_state = final_state.copy() # Create a mutable copy

        # CRITICAL FIX: Remove the 'db' object before serialization
        # The 'db' object is a live connection and cannot be serialized to MongoDB.
        if "db" in serializable_state:
            del serializable_state["db"]

        # CRITICAL FIX: Explicitly include None values when dumping to dictionary
        # This is for MongoDB persistence.
        if serializable_state.get("post_result") and isinstance(serializable_state["post_result"], BaseModel):
            serializable_state["post_result"] = serializable_state["post_result"].model_dump(exclude_none=False)

        # Persist the full state to the 'sessions' collection
        await db.sessions.insert_one({
            "_id": session_id,
            "state": serializable_state, # Use the serializable version
            "created_at": datetime.utcnow()
        })
        logger.info(f"Generated brand suggestions for session {session_id} and persisted state.")
        return BrandSuggestionResponse(session_id=session_id, brand_suggestions=brand_suggestions)

    except Exception as e:
        logger.error(f"AI branding generation failed: {e}", exc_info=True)
        if "MotorCollection object is not callable" in str(e):
             raise HTTPException(status_code=500, detail="Configuration Error: Database collection access is incorrect. Please ensure 'db/session.py' returns the database object and 'api/endpoints/bot.py' uses 'db.collection_name' to access collections.")
        else:
            raise HTTPException(status_code=500, detail=f"AI workflow error: {e}")

@router.post("/continue-post-generation", response_model=ContentGenerationResponse)
async def continue_post_generation(
    request: SelectBrandRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    session_id = request.session_id
    selected_brand = request.selected_brand
    logger.info(f"AI->continue post generation for session {session_id}")

    # Retrieve state from the database and delete it (one-time use session)
    session_doc = await db.sessions.find_one_and_delete({"_id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please restart the process.")

    current_state: BrandingPostState = session_doc["state"]
    # CRITICAL FIX: Re-inject the db dependency for subsequent workflow steps
    # The 'db' object was removed before persistence, so it must be re-added here.
    current_state["db"] = db

    try:
        final_state = await post_graph.ainvoke(current_state)

        caption = final_state.get("base_post")
        image_path = final_state.get("image_path")
        post_result = final_state.get("post_result") # This is expected to be a FacebookPostResponse instance
        
        # CRITICAL FIX: Remove the 'db' object from final_state before any potential re-serialization
        # or if 'final_state' is used elsewhere for persistence.
        if "db" in final_state:
            del final_state["db"]

        if not caption or not image_path:
            raise HTTPException(status_code=500, detail="Failed to generate post content from AI.")
        
        # Direct assignment: If post_result is already a FacebookPostResponse instance, use it directly.
        # Pydantic's response_model will handle its serialization.
        # If for some reason it's a dict, instantiate FacebookPostResponse from it.
        final_facebook_post_response = None
        if isinstance(post_result, FacebookPostResponse):
            final_facebook_post_response = post_result
        elif isinstance(post_result, dict):
            # If it's a dict, instantiate FacebookPostResponse from it.
            # Pydantic will handle Optional fields correctly if the key is missing or value is None.
            final_facebook_post_response = FacebookPostResponse(**post_result)
        
        logger.info(f"Generated full post for session {session_id}.")
        return ContentGenerationResponse(
            caption=caption,
            image_path=image_path,
            post_result=final_facebook_post_response # Pass the correctly constructed instance
        )

    except Exception as e:
        logger.error(f"AI post generation failed for session {session_id}: {e}", exc_info=True)
        if "MotorCollection object is not callable" in str(e):
             raise HTTPException(status_code=500, detail="Configuration Error: Database collection access is incorrect. Please ensure 'db/session.py' returns the database object and 'api/endpoints/bot.py' uses 'db.collection_name' to access collections.")
        else:
            raise HTTPException(status_code=500, detail=f"AI workflow error: {e}")
