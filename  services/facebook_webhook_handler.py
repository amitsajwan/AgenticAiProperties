# services/facebook_webhook_handler.py

import logging
from typing import Dict, Any, List
from db.session import get_db 
from services.social_media.token_service import FacebookTokenService
from models.facebook import FacebookWebhookPayload
from datetime import datetime

logger = logging.getLogger(__name__)

class WebhookHandler:
    async def process_event(self, payload: Dict[str, Any]):
        # Grab the collection
        db_coll = get_db()
        db      = db_coll  # that's your AsyncIOMotorCollection

        for entry in payload.get("entry", []):
            if entry.get("changes"):
                await self._handle_change(entry["changes"][0], db)
            elif entry.get("messaging"):
                await self._handle_message(entry["messaging"][0], db)
            else:
                logger.info(f"Unhandled webhook entry: {entry}")

    async def _handle_change(self, change: Dict[str, Any], db):
        if change["field"] == "feed":
            post_id = change["value"].get("post_id")
            item    = change["value"].get("item")
            verb    = change["value"].get("verb")

            if item == "post" and post_id:
                await self._update_post_status(post_id, verb, db)
            elif item == "comment" and post_id:
                await self._update_comment_count(post_id, db)

    async def _update_post_status(self, post_id: str, action: str, db):
        status_map = {
            "add":    "published",
            "edit":   "updated",
            "delete": "deleted",
            "hide":   "hidden",
            "unhide": "published",
        }
        new_status = status_map.get(action, "modified")

        result = await db.update_one(
            {"facebook.posts.post_id": post_id},
            {"$set": {"facebook.posts.$.status": new_status}}
        )
        if result.modified_count:
            logger.info(f"Post {post_id} status set to {new_status}")
        else:
            logger.warning(f"Post {post_id} not found to update status")

    async def _update_comment_count(self, post_id: str, db):
        # 1) Load post document (to get agent_id)
        doc = await db.find_one(
            {"facebook.posts.post_id": post_id},
            {"facebook.posts.$": 1}
        )
        if not doc or not doc.get("facebook", {}).get("posts"):
            logger.warning(f"No post doc for {post_id}")
            return

        post_rec = doc["facebook"]["posts"][0]
        agent_id = post_rec.get("agent_id")

        # 2) Instantiate token service to decrypt / refresh token
        token_service = FacebookTokenService(db)
        token         = await token_service.get_valid_token(agent_id)

        # 3) Fetch fresh metrics
        metrics_list = await get_post_insights(post_id, token)
        # metrics_list is a List[Dict], you might need to map it to your schema

        # Example: pick the first metric entry (or iterate as needed)
        if metrics_list:
            insights = metrics_list[0].get("values", [])
            # flatten values into a single number if you want, e.g.
            # latest = insights[-1]["value"]
            # else adjust to your data shape

            await db.update_one(
                {"facebook.posts.post_id": post_id},
                {"$set": {
                    "facebook.posts.$.engagement": metrics_list,
                    "facebook.posts.$.last_updated": datetime.utcnow()
                }}
            )
            logger.info(f"Updated engagement for {post_id}")


