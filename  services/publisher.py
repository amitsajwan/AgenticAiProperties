 
from services.website_builder import WebsiteBuilder 

class UnifiedPublisher:
    def __init__(self):
        self.website = WebsiteBuilder()
        
    async def publish(self, agent_id: str, content: dict, platforms: list):
        """Publish to multiple platforms"""
        results = {}
        
        if "website" in platforms:
            # Add to agent's website
            self.website.update_content(agent_id, content)
            results["website"] = f"/agents/{agent_id}/posts/{content['id']}"
        
        if "facebook" in platforms:
            # Publish to Facebook
            fb_result = await facebook_manager.post_property_listing(
                agent_id, 
                content["property_data"]
            )
            results["facebook"] = fb_result.url
            
        return results

