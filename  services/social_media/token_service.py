# services/social_media/token_service.py

import logging
from datetime import datetime, timedelta

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from core.config import settings
from db.session import get_db
# Ensure these models have user_id and page_id fields if you plan to store them
# You might need to add 'user_id', 'page_id', 'page_access_token', 'page_name' fields to FacebookTokenRecord
from models.facebook import FacebookTokenRecord, FacebookPage, TokenStatus

logger = logging.getLogger(__name__)


class FacebookTokenService:
    def __init__(self, db: AsyncIOMotorCollection):
        if not settings.FB_ENCRYPTION_KEY or len(settings.FB_ENCRYPTION_KEY) != 44:
            raise RuntimeError("Invalid or missing FB_ENCRYPTION_KEY")
        self.db = db
        self.cipher = Fernet(settings.FB_ENCRYPTION_KEY.encode())
        self.token_expiry_threshold = timedelta(days=7)

    async def encrypt_token(self, token: str) -> str:
        try:
            return self.cipher.encrypt(token.encode()).decode()
        except Exception:
            logger.exception("Token encryption failed")
            raise HTTPException(500, "Token encryption failed")

    async def decrypt_token(self, encrypted_token: str) -> str:
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            logger.warning("Invalid token decryption attempt")
            raise HTTPException(401, "Invalid access token")
        except Exception:
            logger.exception("Token decryption failed")
            raise HTTPException(500, "Token decryption failed")

    async def exchange_code_for_token(self, code: str, agent_id: str) -> FacebookTokenRecord:
        # Step 1: get short‐lived token
        token_url = f"https://graph.facebook.com/{settings.FB_API_VERSION}/oauth/access_token"
        params = {
            "client_id": settings.FB_APP_ID,
            "redirect_uri": settings.FB_REDIRECT_URI,
            "client_secret": settings.FB_APP_SECRET,
            "code": code,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(token_url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Short‐lived token fetch failed: %s", e.response.text)
            raise HTTPException(400, "Facebook authentication failed")
        except Exception:
            logger.exception("Token exchange HTTP error")
            raise HTTPException(500, "Token exchange failed")

        # Step 2: get long‐lived token
        exchange_params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.FB_APP_ID,
            "client_secret": settings.FB_APP_SECRET,
            "fb_exchange_token": data["access_token"],
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                long_resp = await client.get(token_url, params=exchange_params)
                long_resp.raise_for_status()
                long_data = long_resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Long‐lived token fetch failed: %s", e.response.text)
            raise HTTPException(400, "Facebook token exchange failed")
        except Exception:
            logger.exception("Long‐lived token HTTP error")
            raise HTTPException(500, "Token exchange process failed")

        user_access_token = long_data["access_token"]
        encrypted_user_token = await self.encrypt_token(user_access_token)
        expires_at = datetime.utcnow() + timedelta(seconds=long_data.get("expires_in", 0))

        # Step 3: Get user info and pages to store user_id and relevant page_id
        user_info_url = f"https://graph.facebook.com/{settings.FB_API_VERSION}/me"
        pages_url = f"https://graph.facebook.com/{settings.FB_API_VERSION}/me/accounts"
        
        user_id = None
        page_id = None
        page_access_token = None
        page_name = None # <--- Added for better data storage

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get user ID
                user_info_resp = await client.get(user_info_url, params={"access_token": user_access_token})
                user_info_resp.raise_for_status()
                user_id = user_info_resp.json().get("id")

                # Get pages and find the one configured in settings.FB_PAGE_ID
                pages_resp = await client.get(pages_url, params={"access_token": user_access_token})
                pages_resp.raise_for_status()
                pages_data = pages_resp.json().get("data", [])

                for page in pages_data:
                    # Check if the page ID matches the one configured in settings
                    if page.get("id") == settings.FB_PAGE_ID:
                        page_id = page["id"]
                        page_access_token = page["access_token"]
                        page_name = page.get("name", "") # Get page name
                        break
                
                if not page_id:
                    logger.warning(f"Configured FB_PAGE_ID ({settings.FB_PAGE_ID}) not found among user's pages. Posting will not work without it.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch user info or pages: {e.response.text}", exc_info=True)
            # Do not re-raise, still try to save what we have for debugging
        except Exception:
            logger.exception("Error fetching user info/pages after token exchange")

        record = FacebookTokenRecord(
            access_token=encrypted_user_token,
            expires_at=expires_at,
            status=TokenStatus.ACTIVE,
            scopes=data.get("scope", "").split(","),
            user_id=user_id,
            page_id=page_id,
            page_access_token= await self.encrypt_token(page_access_token) if page_access_token else None,
            page_name=page_name, # <--- Added for better data storage
            created_at=datetime.utcnow() # <--- Added creation timestamp
        )

        # Update the document for the agent, using agent_id as _id
        # The entire record is saved under the document identified by agent_id
        result = await self.db.update_one(
            {"_id": agent_id},
            {"$set": record.model_dump(by_alias=True)}, # Use model_dump for Pydantic v2, by_alias for field names
            upsert=True,
        )

        if not result.acknowledged:
            logger.error("Token storage failed for agent %s", agent_id)
            raise HTTPException(500, "Token storage failed")

        return record

    async def get_valid_token(self, agent_id: str) -> str:
        # This function is intended to get the user's main access token.
        # The token is stored at the root of the agent's document.
        doc = await self.db.find_one(
            {"_id": agent_id},
            {"access_token": 1, "expires_at": 1, "status": 1} # Fetch specific fields
        )
        
        token_data = doc if doc else None # The main token record is at the root
        if not token_data or not token_data.get("access_token"):
            raise HTTPException(404, "No Facebook user token found for this agent.")

        # Ensure datetime object, not string
        expires_at = token_data["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00")) # Handle 'Z' if present
        
        # Check if the token is active
        if token_data.get("status") != TokenStatus.ACTIVE.value:
            raise HTTPException(403, "Facebook user token is not active (e.g., revoked).")

        # Check for expiry, trigger refresh if needed
        if datetime.utcnow() > expires_at - self.token_expiry_threshold:
            logger.info(f"User token for agent {agent_id} is old or near expiry, attempting refresh.")
            # Pass the currently stored encrypted token to refresh
            return await self.refresh_token(agent_id, token_data["access_token"])

        return await self.decrypt_token(token_data["access_token"])

    async def refresh_token(self, agent_id: str, encrypted_token: str) -> str:
        old_user_token = await self.decrypt_token(encrypted_token)
        refresh_url = f"https://graph.facebook.com/{settings.FB_API_VERSION}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.FB_APP_ID,
            "client_secret": settings.FB_APP_SECRET,
            "fb_exchange_token": old_user_token, # Use the decrypted user token to refresh
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(refresh_url, params=params)
                resp.raise_for_status()
                new_data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e.response.text}", exc_info=True)
            raise HTTPException(400, f"Token refresh failed: {e.response.text}")
        except Exception:
            logger.exception("Token refresh HTTP error")
            raise HTTPException(500, "Token refresh process failed")

        new_user_access_token = new_data["access_token"]
        new_encrypted_user_token = await self.encrypt_token(new_user_access_token)
        new_expires = datetime.utcnow() + timedelta(seconds=new_data.get("expires_in", 0))

        # Re-fetch page token data upon user token refresh to ensure it's current
        page_id = None
        page_access_token = None
        page_name = None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                pages_resp = await client.get(f"https://graph.facebook.com/{settings.FB_API_VERSION}/me/accounts", params={"access_token": new_user_access_token})
                pages_resp.raise_for_status()
                pages_data = pages_resp.json().get("data", [])

                for page in pages_data:
                    if page.get("id") == settings.FB_PAGE_ID:
                        page_id = page["id"]
                        page_access_token = page["access_token"]
                        page_name = page.get("name", "")
                        break
        except Exception:
            logger.exception("Error fetching pages during token refresh. Page token data might be outdated.")

        update_fields = {
            "access_token": new_encrypted_user_token, # This is the main user token
            "expires_at": new_expires,
            "last_refreshed": datetime.utcnow(),
            "status": TokenStatus.ACTIVE.value # Ensure status is active after successful refresh
        }
        if page_id and page_access_token:
            update_fields["page_id"] = page_id
            update_fields["page_access_token"] = await self.encrypt_token(page_access_token)
            update_fields["page_name"] = page_name

        update = await self.db.update_one(
            {"_id": agent_id},
            {"$set": update_fields},
        )
        if not update.modified_count:
            logger.error("Failed to update refreshed token for agent %s. Document might not exist.", agent_id)
            # This could happen if the initial auth never completed for this agent_id.
            raise HTTPException(500, "Failed to update token in database during refresh.")

        return new_user_access_token # Return the decrypted user token

    async def revoke_token(self, agent_id: str) -> bool:
        res = await self.db.update_one(
            {"_id": agent_id},
            {"$set": {"status": TokenStatus.REVOKED.value}} # Update status at root level of the document
        )
        return res.modified_count > 0

    async def validate_permissions(self, agent_id: str) -> bool:
        try:
            # This function uses get_valid_token, which returns user token.
            # Permissions are linked to user token, not page token.
            token = await self.get_valid_token(agent_id)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://graph.facebook.com/{settings.FB_API_VERSION}/me/permissions",
                    params={"access_token": token}
                )
                resp.raise_for_status()
                perms = {p["permission"]: p["status"] for p in resp.json().get("data", [])}
                required = ["pages_manage_posts", "pages_read_engagement", "pages_show_list"] # Add pages_show_list
                return all(perms.get(p) == "granted" for p in required)
        except Exception:
            logger.exception("Permission validation error")
            return False

    async def get_page_token_for_agent(self, agent_id: str) -> FacebookPage:
        # Load the entire agent document to get user and page tokens
        doc = await self.db.find_one(
            {"_id": agent_id},
            # Fetch all necessary fields including page_id, page_access_token, and page_name
            {"page_id": 1, "page_access_token": 1, "page_name": 1, "created_at": 1, "user_id": 1}
        )

        if not doc:
            raise HTTPException(404, "No Facebook configuration found for this agent.")
        
        page_id = doc.get("page_id")
        encrypted_page_token = doc.get("page_access_token")
        page_name = doc.get("page_name", "Unknown Page")
        connected_at = doc.get("created_at", datetime.utcnow()) # Using created_at of the agent record for connection time
        # You might need to make another API call to get followers if not stored with page_id initially
        
        if not page_id or not encrypted_page_token:
            # This case means the initial authentication didn't fetch/store page data correctly
            raise HTTPException(404, "Facebook page ID or page access token not found for this agent. Please re-authenticate.")
        
        decrypted_page_token = await self.decrypt_token(encrypted_page_token)

        return FacebookPage(
            page_id=page_id,
            name=page_name,
            access_token=decrypted_page_token,
            category=doc.get("page_category"), # Assuming you might save this if fetched
            connected_at=connected_at,
            followers=doc.get("page_followers") # Assuming you might save this if fetched
        )


async def get_token_service(
    db: AsyncIOMotorCollection = Depends(get_db)
) -> FacebookTokenService:
    """
    FastAPI dependency to inject a configured FacebookTokenService.
    """
    return FacebookTokenService(db)

