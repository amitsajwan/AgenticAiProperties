import os
from jinja2 import Environment, FileSystemLoader
from models.agents import AgentBranding

class WebsiteBuilder:
    def __init__(self):
        self.template_dir = "templates/websites"
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
    def generate_website(self, agent_id: str, branding: AgentBranding) -> str:
        template = self.env.get_template(f"{branding.website_template}.html")
        
        # Create website structure
        website = template.render(
            agent_name=branding.agent_name,
            description=branding.description,
            primary_color=branding.primary_color,
            secondary_color=branding.secondary_color,
            logo_url=branding.logo_url or "/static/default-logo.png",
            contact_email=branding.contact_email,
            phone=branding.phone,
            areas=", ".join(branding.service_areas),
            specialization=branding.specialization
        )
        
        # Save to agent's directory
        os.makedirs(f"agent_sites/{agent_id}", exist_ok=True)
        with open(f"agent_sites/{agent_id}/index.html", "w") as f:
            f.write(website)
            
        return f"/agents/{agent_id}"

    def update_content(self, agent_id: str, content: dict):
        """Add generated content to agent's website"""
        # Implementation for adding posts/properties
        pass

