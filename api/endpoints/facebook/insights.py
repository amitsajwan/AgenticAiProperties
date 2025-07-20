import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from db.session import get_db
# CRITICAL FIX: Changed import name from FacebookAnalytics to FacebookAnalyticsService
from services.facebook_analytics import FacebookAnalyticsService, get_facebook_analytics_service 

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/agents/{agent_id}")
async def get_agent_insights(
    agent_id: str,
    days: int = 7, # Default to 7 days for analytics
    analytics_service: FacebookAnalyticsService = Depends(get_facebook_analytics_service)
):
    """
    Retrieve aggregated Facebook insights for a specific agent.
    """
    logger.info(f"Fetching aggregated insights for agent: {agent_id} for the last {days} days.")
    try:
        analytics_data = await analytics_service.get_agent_analytics(agent_id, days)
        return analytics_data
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching agent insights for {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch insights: {e}")

@router.get("/posts/{post_id}")
async def get_post_insights(
    post_id: str,
    # This endpoint needs an access token to call Facebook Graph API.
    # You'll need a way to get the page access token for the post's agent.
    # For now, it's a placeholder.
    analytics_service: FacebookAnalyticsService = Depends(get_facebook_analytics_service)
):
    """
    Retrieve detailed insights for a specific Facebook post.
    NOTE: This requires a valid page access token to be passed or retrieved internally.
    """
    logger.info(f"Fetching detailed insights for post: {post_id}")
    # This part would typically involve calling Facebook Graph API with a page access token
    # For demonstration, returning dummy data or an error if not implemented.
    # You would need to fetch the page_access_token for the agent associated with this post_id.
    
    # Example placeholder:
    # try:
    #     # Assuming you have a way to get the page_access_token for this post_id
    #     # page_access_token = await token_service.get_page_token_for_post(post_id) 
    #     insights = await analytics_service.get_post_insights(post_id, "dummy_access_token") # Replace dummy
    #     return insights
    # except Exception as e:
    #     logger.error(f"Error fetching post insights: {e}", exc_info=True)
    #     raise HTTPException(status_code=500, detail="Failed to fetch post insights.")
    
    return {"message": "Post insights endpoint is a placeholder and requires page access token implementation.", "post_id": post_id}

