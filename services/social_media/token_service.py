import logging
from datetime import datetime, timedelta

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase # Correct import for database object

from core.config import settings
from db.session import get_db
# Ensure these models have user_id and page_id fields if you plan to store them
# You might need to add 'user_id', 'page_id', 'page_access_token', 'page_name' fields to FacebookTokenRecord
from models.facebook import FacebookTokenRecord, FacebookPage, TokenStatus

logger = logging.getLogger(__name__)


class FacebookTokenService:
    def __init__(self, db: AsyncIOMotorDatabase):
        if not settings.FB_ENCRYPTION_KEY or len(settings.FB_ENCRYPTION_KEY) != 44:
            raise RuntimeError("Invalid or missing FB_ENCRYPTION_KEY")
        self.db = db
        # Access the specific collection where tokens are stored
        # Assuming 'facebook_tokens' is your collection name for storing Facebook credentials
        self.token_collection = self.db.facebook_tokens 
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
        logger.info(f"[{agent_id}] Starting Facebook code exchange for token.")
        # Step 1: get short‐lived token
        token_url = f"https://graph.facebook.com/{settings.FB_API_VERSION}/oauth/access_token"
        params = {
            "client_id": settings.FB_APP_ID,
            "redirect_uri": settings.FB_REDIRECT_URI,
            "client_secret": settings.FB_APP_SECRET,
            "code": code,
        }
        try:
            logger.info(f"[{agent_id}] Requesting short-lived token from Facebook.")
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(token_url, params=params)
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"[{agent_id}] Short-lived token received. Expires in: {data.get('expires_in')}s")
        except httpx.HTTPStatusError as e:
            logger.error(f"[{agent_id}] Short-lived token fetch failed: {e.response.text}", exc_info=True)
            raise HTTPException(400, "Facebook authentication failed")
        except Exception:
            logger.exception(f"[{agent_id}] Token exchange HTTP error during short-lived token fetch.")
            raise HTTPException(500, "Token exchange failed")

        # Step 2: get long‐lived token
        exchange_params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.FB_APP_ID,
            "client_secret": settings.FB_APP_SECRET,
            "fb_exchange_token": data["access_token"],
        }
        try:
            logger.info(f"[{agent_id}] Exchanging for long-lived token.")
            async with httpx.AsyncClient(timeout=10.0) as client:
                long_resp = await client.get(token_url, params=exchange_params)
                long_resp.raise_for_status()
                long_data = long_resp.json()
                logger.info(f"[{agent_id}] Long-lived token received. Expires in: {long_data.get('expires_in')}s")
        except httpx.HTTPStatusError as e:
            logger.error(f"[{agent_id}] Long-lived token fetch failed: {e.response.text}", exc_info=True)
            raise HTTPException(400, "Facebook token exchange failed")
        except Exception:
            logger.exception(f"[{agent_id}] Long-lived token HTTP error.")
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
        page_name = None 

        try:
            logger.info(f"[{agent_id}] Fetching user info and pages from Facebook.")
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get user ID
                user_info_resp = await client.get(user_info_url, params={"access_token": user_access_token})
                user_info_resp.raise_for_status()
                user_id = user_info_resp.json().get("id")
                logger.info(f"[{agent_id}] User ID fetched: {user_id}")

                # Get pages and find the one configured in settings.FB_PAGE_ID
                pages_resp = await client.get(pages_url, params={"access_token": user_access_token})
                pages_resp.raise_for_status()
                pages_data = pages_resp.json().get("data", [])
                
                logger.info(f"[{agent_id}] Configured FB_PAGE_ID: '{settings.FB_PAGE_ID}'")
                logger.info(f"[{agent_id}] Pages returned by Facebook (IDs): {[p.get('id') for p in pages_data]}")
                logger.info(f"[{agent_id}] Pages returned by Facebook (Names): {[p.get('name') for p in pages_data]}")


                for page in pages_data:
                    logger.info(f"[{agent_id}] Checking page: ID='{page.get('id')}', Name='{page.get('name')}', Access Token Present: {bool(page.get('access_token'))}")
                    if page.get("id") == settings.FB_PAGE_ID:
                        page_id = page["id"]
                        page_access_token = page["access_token"]
                        page_name = page.get("name", "") 
                        logger.info(f"[{agent_id}] MATCH FOUND! Configured FB_PAGE_ID matches page: ID='{page_id}', Name='{page_name}'")
                        break
                
                if not page_id:
                    logger.warning(f"[{agent_id}] Configured FB_PAGE_ID ('{settings.FB_PAGE_ID}') not found among user's pages. Posting will not work without it.")
                elif not page_access_token:
                    logger.warning(f"[{agent_id}] Page ID '{page_id}' found, but no page access token was returned. Check page permissions.")

        except httpx.HTTPStatusError as e:
            logger.error(f"[{agent_id}] Failed to fetch user info or pages from Facebook: {e.response.text}", exc_info=True)
            # Do not re-raise, still try to save what we have for debugging
        except Exception:
            logger.exception(f"[{agent_id}] Error fetching user info/pages after token exchange.")

        # Only encrypt page_access_token if it's not None
        encrypted_page_access_token = await self.encrypt_token(page_access_token) if page_access_token else None

        record = FacebookTokenRecord(
            access_token=encrypted_user_token,
            expires_at=expires_at,
            status=TokenStatus.ACTIVE,
            scopes=data.get("scope", "").split(","),
            user_id=user_id,
            page_id=page_id,
            page_access_token=encrypted_page_access_token, # Use the potentially None encrypted token
            page_name=page_name, 
            created_at=datetime.utcnow() 
        )

        # Update the document for the agent, using agent_id as _id
        # The entire record is saved under the document identified by agent_id
        result = await self.token_collection.update_one(
            {"_id": agent_id},
            {"$set": record.model_dump(by_alias=True)}, # Use model_dump for Pydantic v2, by_alias for field names
            upsert=True,
        )

        if not result.acknowledged:
            logger.error(f"[{agent_id}] Token storage failed for agent %s. Acknowledgment was False.", agent_id)
            raise HTTPException(500, "Token storage failed")
        
        logger.info(f"[{agent_id}] Facebook token record saved/updated in DB for agent.")

        return record

    async def get_valid_token(self, agent_id: str) -> str:
        logger.info(f"[{agent_id}] Attempting to retrieve valid user token.")
        doc = await self.token_collection.find_one(
            {"_id": agent_id},
            {"access_token": 1, "expires_at": 1, "status": 1} # Fetch specific fields
        )
        
        token_data = doc if doc else None
        if not token_data or not token_data.get("access_token"):
            logger.warning(f"[{agent_id}] No Facebook user token found in DB.")
            raise HTTPException(404, "No Facebook user token found for this agent.")

        expires_at = token_data["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00")) 
        
        if token_data.get("status") != TokenStatus.ACTIVE.value:
            logger.warning(f"[{agent_id}] Facebook user token is not active (status: {token_data.get('status')}).")
            raise HTTPException(403, "Facebook user token is not active (e.g., revoked).")

        if datetime.utcnow() > expires_at - self.token_expiry_threshold:
            logger.info(f"[{agent_id}] User token is old or near expiry, attempting refresh.")
            return await self.refresh_token(agent_id, token_data["access_token"])

        logger.info(f"[{agent_id}] Returning valid decrypted user token.")
        return await self.decrypt_token(token_data["access_token"])

    async def refresh_token(self, agent_id: str, encrypted_token: str) -> str:
        logger.info(f"[{agent_id}] Attempting to refresh user token.")
        old_user_token = await self.decrypt_token(encrypted_token)
        refresh_url = f"https://graph.facebook.com/{settings.FB_API_VERSION}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.FB_APP_ID,
            "client_secret": settings.FB_APP_SECRET,
            "fb_exchange_token": old_user_token,
        }
        try:
            logger.info(f"[{agent_id}] Requesting new long-lived token from Facebook.")
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(refresh_url, params=params)
                resp.raise_for_status()
                new_data = resp.json()
                logger.info(f"[{agent_id}] New long-lived token received. Expires in: {new_data.get('expires_in')}s")
        except httpx.HTTPStatusError as e:
            logger.error(f"[{agent_id}] Token refresh failed: {e.response.text}", exc_info=True)
            raise HTTPException(400, f"Token refresh failed: {e.response.text}")
        except Exception:
            logger.exception(f"[{agent_id}] Token refresh HTTP error.")
            raise HTTPException(500, "Token refresh process failed")

        new_user_access_token = new_data["access_token"]
        new_encrypted_user_token = await self.encrypt_token(new_user_access_token)
        new_expires = datetime.utcnow() + timedelta(seconds=new_data.get("expires_in", 0))

        # Re-fetch page token data upon user token refresh to ensure it's current
        page_id = None
        page_access_token = None
        page_name = None

        try:
            logger.info(f"[{agent_id}] Re-fetching pages during token refresh.")
            async with httpx.AsyncClient(timeout=10.0) as client:
                pages_resp = await client.get(f"https://graph.facebook.com/{settings.FB_API_VERSION}/me/accounts", params={"access_token": new_user_access_token})
                pages_resp.raise_for_status()
                pages_data = pages_resp.json().get("data", [])

                logger.info(f"[{agent_id}] Configured FB_PAGE_ID during refresh: '{settings.FB_PAGE_ID}'")
                logger.info(f"[{agent_id}] Pages returned by Facebook during refresh (IDs): {[p.get('id') for p in pages_data]}")

                for page in pages_data:
                    logger.info(f"[{agent_id}] Checking page during refresh: ID='{page.get('id')}', Name='{page.get('name')}'")
                    if page.get("id") == settings.FB_PAGE_ID:
                        page_id = page["id"]
                        page_access_token = page["access_token"]
                        page_name = page.get("name", "")
                        logger.info(f"[{agent_id}] MATCH FOUND during refresh! Page ID: '{page_id}', Name: '{page_name}'")
                        break
        except Exception:
            logger.exception(f"[{agent_id}] Error fetching pages during token refresh. Page token data might be outdated.")

        update_fields = {
            "access_token": new_encrypted_user_token,
            "expires_at": new_expires,
            "last_refreshed": datetime.utcnow(),
            "status": TokenStatus.ACTIVE.value
        }
        if page_id and page_access_token:
            update_fields["page_id"] = page_id
            update_fields["page_access_token"] = await self.encrypt_token(page_access_token)
            update_fields["page_name"] = page_name
            logger.info(f"[{agent_id}] Updating DB with new page token data.")
        else:
            logger.warning(f"[{agent_id}] No page_id or page_access_token found during refresh. Page credentials will not be updated.")


        update = await self.token_collection.update_one(
            {"_id": agent_id},
            {"$set": update_fields},
        )
        if not update.modified_count:
            logger.error(f"[{agent_id}] Failed to update refreshed token for agent. Document might not exist or no changes made.", agent_id)
            raise HTTPException(500, "Failed to update token in database during refresh.")
        
        logger.info(f"[{agent_id}] User token refreshed and DB updated.")

        return new_user_access_token

    async def revoke_token(self, agent_id: str) -> bool:
        logger.info(f"[{agent_id}] Attempting to revoke token.")
        res = await self.token_collection.update_one(
            {"_id": agent_id},
            {"$set": {"status": TokenStatus.REVOKED.value}}
        )
        if res.modified_count > 0:
            logger.info(f"[{agent_id}] Token status set to REVOKED.")
        else:
            logger.warning(f"[{agent_id}] Token for revocation not found or already revoked.")
        return res.modified_count > 0

    async def validate_permissions(self, agent_id: str) -> bool:
        logger.info(f"[{agent_id}] Validating Facebook permissions.")
        try:
            token = await self.get_valid_token(agent_id)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://graph.facebook.com/{settings.FB_API_VERSION}/me/permissions",
                    params={"access_token": token}
                )
                resp.raise_for_status()
                perms = {p["permission"]: p["status"] for p in resp.json().get("data", [])}
                required = ["pages_manage_posts", "pages_read_engagement", "pages_show_list"]
                
                is_granted = all(perms.get(p) == "granted" for p in required)
                if is_granted:
                    logger.info(f"[{agent_id}] All required permissions are granted.")
                else:
                    missing_perms = [p for p in required if perms.get(p) != "granted"]
                    logger.warning(f"[{agent_id}] Missing or not granted permissions: {missing_perms}")
                return is_granted
        except Exception:
            logger.exception(f"[{agent_id}] Permission validation error.")
            return False

    async def get_page_token_for_agent(self, agent_id: str) -> FacebookPage:
        logger.info(f"[{agent_id}] Attempting to retrieve page token for agent.")
        doc = await self.token_collection.find_one(
            {"_id": agent_id},
            {"page_id": 1, "page_access_token": 1, "page_name": 1, "created_at": 1, "user_id": 1}
        )

        if not doc:
            logger.warning(f"[{agent_id}] No Facebook configuration found in DB for this agent.")
            raise HTTPException(404, "No Facebook configuration found for this agent.")
        
        page_id = doc.get("page_id")
        encrypted_page_token = doc.get("page_access_token")
        page_name = doc.get("page_name", "Unknown Page")
        connected_at = doc.get("created_at", datetime.utcnow())
        
        if not page_id or not encrypted_page_token:
            logger.warning(f"[{agent_id}] Facebook page ID ('{page_id}') or page access token (present: {bool(encrypted_page_token)}) not found in DB for this agent. Re-authentication likely needed.")
            raise HTTPException(404, "Facebook page ID or page access token not found for this agent. Please re-authenticate.")
        
        decrypted_page_token = await self.decrypt_token(encrypted_page_token)
        logger.info(f"[{agent_id}] Successfully retrieved and decrypted page token for page ID: '{page_id}'.")

        return FacebookPage(
            page_id=page_id,
            name=page_name,
            access_token=decrypted_page_token,
            category=doc.get("page_category"), 
            connected_at=connected_at,
            followers=doc.get("page_followers") 
        )


async def get_token_service(
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> FacebookTokenService:
    """
    FastAPI dependency to inject a configured FacebookTokenService.
    """
    return FacebookTokenService(db)
