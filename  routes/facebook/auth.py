from fastapi import APIRouter, Request
from pymongo import MongoClient
import logging
from datetime import datetime

# Logger setup
logger = logging.getLogger("facebook_auth")
logger.setLevel(logging.INFO)

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["property_agents"]
tokens_collection = db["facebook_tokens"]

router = APIRouter()

@router.get("/facebook/auth/login")
async def start_oauth(agent_id: str):
    logger.info(f"[FBAuth] Starting OAuth flow for {agent_id}")
    redirect_url = f"https://www.facebook.com/v19.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=YOUR_CALLBACK_URI&state={agent_id}"
    return { "redirect": redirect_url }

@router.get("/facebook/auth/callback")
async def handle_oauth_callback(request: Request):
    agent_id = request.query_params.get("state")
    access_token = request.query_params.get("access_token", "mock_token")
    page_id = "mock_page_456"  # Simulated value

    logger.info(f"[FBAuth] OAuth callback received for {agent_id}")

    record = {
        "agent_id": agent_id,
        "access_token": access_token,
        "page_id": page_id,
        "permissions_ok": True,
        "connected_at": datetime.utcnow()
    }

    try:
        tokens_collection.update_one(
            { "agent_id": agent_id },
            { "$set": record },
            upsert=True
        )
        logger.info(f"[FBAuth] Saved token info for {agent_id}")
    except Exception as e:
        logger.error(f"[FBAuth] Failed to save token for {agent_id}: {str(e)}")

    return { "status": "connected", "agent_id": agent_id }

