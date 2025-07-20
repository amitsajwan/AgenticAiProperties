import logging
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from fastapi import Depends, HTTPException

from db.session import get_db

logger = logging.getLogger(__name__)

class FacebookAnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # CRITICAL FIX: Specify the collection for aggregation
        # Assuming your Facebook posts data is stored in the 'facebook_posts' collection
        self.posts_collection: AsyncIOMotorCollection = db.facebook_posts 
        logger.info("FacebookAnalyticsService initialized.")

    async def get_agent_analytics(self, agent_id: str, days: int = 7):
        logger.info(f"Running analytics aggregation for agent {agent_id}")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "agent_id": agent_id,
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "status": "published" # Only analyze published posts
                }
            },
            {
                "$group": {
                    "_id": None, # Group all matching documents
                    "total_posts": {"$sum": 1},
                    "total_likes": {"$sum": "$engagement.likes"},
                    "total_comments": {"$sum": "$engagement.comments"},
                    "total_shares": {"$sum": "$engagement.shares"},
                    "total_impressions": {"$sum": "$engagement.impressions"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_posts": 1,
                    "total_likes": {"$ifNull": ["$total_likes", 0]},
                    "total_comments": {"$ifNull": ["$total_comments", 0]},
                    "total_shares": {"$ifNull": ["$total_shares", 0]},
                    "total_impressions": {"$ifNull": ["$total_impressions", 0]}
                }
            }
        ]

        try:
            # CRITICAL FIX: Call aggregate on the specific collection (self.posts_collection)
            results = await self.posts_collection.aggregate(pipeline).to_list(length=None)
            
            if results:
                analytics_data = results[0]
                logger.info(f"Aggregation successful for agent {agent_id}: {analytics_data}")
                return analytics_data
            else:
                logger.info(f"No analytics data found for agent {agent_id} in the last {days} days.")
                return {
                    "total_posts": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "total_impressions": 0
                }
        except Exception as e:
            logger.error(f"Aggregation failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {e}")

async def get_facebook_analytics_service(
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> FacebookAnalyticsService:
    """
    FastAPI dependency to inject a configured FacebookAnalyticsService.
    """
    return FacebookAnalyticsService(db)
