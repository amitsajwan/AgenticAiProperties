from pydantic import BaseModel, Field
from typing import Optional

class AgentBranding(BaseModel):
    agent_name: str = Field(..., max_length=50, description="Public-facing agent name")
    description: str = Field(..., max_length=500, description="Agent bio/description")
    specialization: str = Field(..., max_length=100, description="Real estate specialization")
    service_areas: list[str] = Field(default_factory=list, description="Service regions")
    primary_color: str = Field("#4361ee", description="Brand primary color")
    secondary_color: str = Field("#3f37c9", description="Brand secondary color")
    logo_url: Optional[str] = Field(None, description="URL to agent logo")
    contact_email: str = Field(..., description="Contact email")
    phone: str = Field(..., description="Contact phone")

class AgentProfile(AgentBranding):
    website_template: str = Field("default", description="Website template name")
    social_links: dict = Field(default_factory=dict, description="Social media profiles")
    ai_tone: str = Field("professional", description="Preferred AI writing tone")

