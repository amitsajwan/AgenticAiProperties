# api/endpoints/facebook/insights.py

from fastapi import APIRouter, Query, Depends
from services.facebook_analytics import FacebookAnalytics
from db.session import get_db
from motor.motor_asyncio import AsyncIOMotorCollection

router = APIRouter()

@router.get("/agents/{agent_id}")
async def get_agent_insights(
    agent_id: str,
    days: int = Query(7, ge=1, le=30),
    db: AsyncIOMotorCollection = Depends(get_db)
):
    from datetime import datetime, timedelta
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    analytics = FacebookAnalytics(db)
    return await analytics.get_agent_analytics(agent_id, start_date, end_date)


