# services/facebook_analytics.py

import logging
import httpx
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FacebookAnalytics:
    def __init__(self, db: AsyncIOMotorCollection):
        self.db = db

    async def get_agent_analytics(self, agent_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Aggregate insights for an agent's posts over a date range.
        """
        pipeline = [
            {
                "$match": {
                    "agent_id": agent_id,
                    "date": { "$gte": start_date, "$lte": end_date }
                }
            },
            {
                "$group": {
                    "_id": "$date",
                    "likes": { "$sum": "$likes" },
                    "comments": { "$sum": "$comments" },
                    "shares": { "$sum": "$shares" },
                    "impressions": { "$sum": "$impressions" }
                }
            },
            { "$sort": { "_id": 1 } }
        ]

        try:
            logger.info(f"Running analytics aggregation for agent {agent_id}")
            results = await self.db.aggregate(pipeline).to_list(length=None)
            return [
                {
                    "date": r["_id"],
                    "likes": r["likes"],
                    "comments": r["comments"],
                    "shares": r["shares"],
                    "impressions": r["impressions"]
                } for r in results
            ]
        except Exception as e:
            logger.error(f"Aggregation failed: {e}", exc_info=True)
            return []

    async def get_post_insights(self, post_id: str, access_token: str) -> List[Dict[str, Any]]:
        """
        Fetch insights for a specific Facebook post via Graph API.
        """
        url = f"https://graph.facebook.com/v18.0/{post_id}/insights"
        params = {
            "metric": "post_impressions,post_engaged_users,post_clicks",
            "access_token": access_token
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"Facebook API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch post insights: {e}", exc_info=True)
            return []


