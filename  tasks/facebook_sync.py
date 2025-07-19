import asyncio
import logging
from datetime import datetime, timedelta
from services.social_media.facebook_manager import facebook_manager
from services.social_media.token_service import token_service
from db.session import get_db

logger = logging.getLogger(__name__)

class FacebookSync:
    def __init__(self):
        self.db = get_db().agents

    async def refresh_all_tokens(self):
        agents = self.db.find({"facebook.token.expires_at": {
            "$lt": datetime.now() + timedelta(days=7)
        }})
        
        async for agent in agents:
            try:
                await token_service.get_valid_token(agent['_id'])
            except Exception as e:
                logger.error(f"Failed to refresh token for agent {agent['_id']}: {str(e)}")

    async def sync_post_engagements(self):
        agents = self.db.find({"facebook.posts.status": "published"})
        
        async for agent in agents:
            for post in agent.get('facebook', {}).get('posts', []):
                if post['status'] == 'published':
                    try:
                        insights = await facebook_manager.get_post_insights(post['post_id'])
                        await self.db.update_one(
                            {"_id": agent['_id'], "facebook.posts.post_id": post['post_id']},
                            {"$set": {"facebook.posts.$.engagement": insights}}
                        )
                    except Exception as e:
                        logger.error(f"Failed to sync insights for post {post['post_id']}: {str(e)}")

    async def run_scheduled_tasks(self):
        while True:
            await self.refresh_all_tokens()
            await self.sync_post_engagements()
            await asyncio.sleep(3600)  # Run hourly

