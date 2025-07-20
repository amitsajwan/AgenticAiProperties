# models/agent.py

from pydantic import BaseModel, Field
from typing import List, Optional
from models.facebook import FacebookPostResponse # Import FacebookPostResponse

class AgentWebsite(BaseModel):
    agent_id: str
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None 
    cover_image_url: Optional[str] = None
    posts: List[FacebookPostResponse] = []
    # Field for logo generation prompt - not stored directly in DB, but used for logic
    logo_prompt: Optional[str] = Field(None, description="Prompt for AI logo generation")

