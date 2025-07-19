 

import asyncio                # ← ADD THIS
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import os
import httpx
import secrets
import logging
from datetime import datetime
from core.config import settings
from services.social_media.token_service import FacebookTokenService, get_token_service
from db.session import get_db
from motor.motor_asyncio import AsyncIOMotorCollection

import logging
import secrets
from datetime import datetime

import httpx
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import RedirectResponse

from core.config import settings
from services.social_media.token_service import FacebookTokenService, get_token_service



router = APIRouter()
logger = logging.getLogger(__name__)

# Use settings from configuration
FB_OAUTH_REDIRECT_URI = settings.FB_REDIRECT_URI
FB_APP_ID = settings.FB_APP_ID

# State token management for CSRF protection
state_tokens = {}

@router.get("/login")
async def login(request: Request, agent_id: str = Query(...)):
    """
    Initiate Facebook OAuth login flow
    """
    try:
        state_token = secrets.token_urlsafe(32)
        state_tokens[state_token] = {
            "agent_id": agent_id,
            "created_at": datetime.utcnow(),
            "ip": request.client.host if request.client else "unknown"
        }
        fb_oauth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={FB_APP_ID}&"
            f"redirect_uri={FB_OAUTH_REDIRECT_URI}&"
            f"state={state_token}&"
            f"scope=pages_show_list,pages_read_engagement,"
            f"pages_manage_posts,pages_manage_metadata,"
            f"pages_read_user_content"
        )
        return RedirectResponse(url=fb_oauth_url)
    except Exception as e:
        logger.error(f"Login initiation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login initialization failed")

@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    error_reason: str = Query(None),
    error_description: str = Query(None),
    token_service: FacebookTokenService = Depends(get_token_service)
):
    """
    Handle Facebook OAuth callback: exchange code for token,
    then redirect back to your Next.js dashboard.
    """
    # 1) Validate state token…
    state_data = state_tokens.pop(state, None)
    if not state_data:
        logger.warning(f"Invalid state token: {state}")
        raise HTTPException(status_code=400, detail="Invalid state token")
    if (datetime.utcnow() - state_data["created_at"]).total_seconds() > 300:
        logger.warning("Expired state token")
        raise HTTPException(status_code=400, detail="Expired state token")

    if error:
        logger.error(f"Facebook OAuth error: {error_reason} - {error_description}")
        raise HTTPException(status_code=400, detail=f"Authorization failed: {error_reason}")

    agent_id = state_data["agent_id"]

    # 2) Exchange code for long‐lived token & store
    try:
        token_record = await token_service.exchange_code_for_token(code, agent_id)
    except Exception as e:
        logger.error(f"Token exchange failed: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Facebook token exchange failed")

    # 3) Redirect back to your dashboard with a success flag
    redirect_to = (
        f"{settings.FRONTEND_URL}/dashboard"
        f"?agent_id={agent_id}"
        f"&status=success"
        f"&expires_at={token_record.expires_at.isoformat()}"
    )
    return RedirectResponse(url=redirect_to, status_code=302)



@router.get("/me")
async def get_me(
    token: str = Query(...),
    token_service: FacebookTokenService = Depends(get_token_service)
):
    """
    Get current user info
    """
    try:
        decrypted_token = await token_service.decrypt_token(token)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://graph.facebook.com/v18.0/me",
                params={"access_token": decrypted_token, "fields": "id,name,email"}
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        detail = "Invalid or expired token" if status == 400 else "Failed to fetch user info"
        logger.error(f"Facebook API error: {status} - {e.response.text}")
        raise HTTPException(status_code=status, detail=detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User info fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user information")

async def clean_expired_tokens():
    """
    Periodically clean expired state tokens
    """
    while True:
        try:
            now = datetime.utcnow()
            expired = [
                token for token, data in state_tokens.items()
                if (now - data["created_at"]).total_seconds() > 300
            ]
            for token in expired:
                state_tokens.pop(token, None)
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Token cleanup failed: {e}", exc_info=True)
            await asyncio.sleep(60)


