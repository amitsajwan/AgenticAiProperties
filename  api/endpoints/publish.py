from fastapi import APIRouter
from services.publisher import UnifiedPublisher

router = APIRouter()
publisher = UnifiedPublisher()

@router.post("")
async def publish_content(
    agent_id: str, 
    content: dict,
    platforms: list = ["website", "facebook"]
):
    """Publish content to multiple platforms"""
    results = await publisher.publish(agent_id, content, platforms)
    return {
        "status": "published",
        "results": results,
        "message": "Content published successfully"
    }

