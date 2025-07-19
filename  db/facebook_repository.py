# db/facebook_repository.py

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from bson.objectid import ObjectId

from models.facebook import (
    FacebookPost,
    FacebookPostUpdate,
    FacebookTokenRecord,
    FacebookPage
)

logger = logging.getLogger(__name__)


class FacebookRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        self.posts_path = "facebook.posts"
        self.tokens_path = "facebook.tokens"
        self.pages_path = "facebook.pages"

    async def log_post(self, post: FacebookPost) -> FacebookPost:
        try:
            post_dict = post.dict()
            post_dict["logged_at"] = datetime.utcnow()

            logger.info(f"Inserting post for agent: {post.agent_id}")
            logger.debug(f"Post payload: {post_dict}")

            result = await self.collection.update_one(
                {"_id": post.agent_id},
                {"$push": {self.posts_path: post_dict}},
                upsert=True
            )

            if not result.acknowledged:
                raise ValueError("Post insertion was not acknowledged by MongoDB.")

            logger.info(f"Post logged successfully. Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted: {result.upserted_id}")
            return post

        except Exception as e:
            logger.error(f"Error logging Facebook post: {e}", exc_info=True)
            raise

    async def update_post(self, agent_id: str, post_id: str, update: FacebookPostUpdate) -> FacebookPost:
        try:
            update_data = {"$set": {}}
            for field, value in update.dict(exclude_unset=True).items():
                update_data["$set"][f"{self.posts_path}.$.{field}"] = value

            if update.status:
                update_data["$set"][f"{self.posts_path}.$.last_updated"] = datetime.utcnow()

            logger.info(f"Updating post: {post_id} for agent: {agent_id} with data: {update_data}")

            result = await self.collection.find_one_and_update(
                {
                    "_id": agent_id,
                    f"{self.posts_path}.post_id": post_id
                },
                update_data,
                return_document=ReturnDocument.AFTER
            )

            if not result:
                raise ValueError(f"Post {post_id} not found for agent {agent_id}")

            post_list = result.get("facebook", {}).get("posts", [])
            updated_post = next((p for p in post_list if p["post_id"] == post_id), None)

            if not updated_post:
                raise ValueError("Post updated but not found in returned document")

            return FacebookPost(**updated_post)

        except Exception as e:
            logger.error(f"Error updating Facebook post: {e}", exc_info=True)
            raise

    async def store_token(self, agent_id: str, token: FacebookTokenRecord) -> FacebookTokenRecord:
        try:
            token_dict = token.dict()
            token_dict["last_updated"] = datetime.utcnow()

            logger.info(f"Storing token for agent: {agent_id}")

            result = await self.collection.update_one(
                {"_id": agent_id},
                {"$set": {self.tokens_path: token_dict}},
                upsert=True
            )

            if not result.acknowledged:
                raise ValueError("Token storage not acknowledged")

            return token

        except Exception as e:
            logger.error(f"Error storing token: {e}", exc_info=True)
            raise

    async def store_page(self, agent_id: str, page: FacebookPage) -> FacebookPage:
        try:
            page_dict = page.dict()
            page_dict["connected_at"] = datetime.utcnow()

            logger.info(f"Storing page info for agent: {agent_id}")

            result = await self.collection.update_one(
                {"_id": agent_id},
                {"$set": {self.pages_path: page_dict}},
                upsert=True
            )

            if not result.acknowledged:
                raise ValueError("Page storage not acknowledged")

            return page

        except Exception as e:
            logger.error(f"Error storing Facebook page: {e}", exc_info=True)
            raise


