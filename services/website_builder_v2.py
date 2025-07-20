import logging
import os
from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from jinja2 import Environment, FileSystemLoader

from models.facebook import FacebookPostResponse 
from models.agent import AgentWebsite

logger = logging.getLogger(__name__)

class WebsiteBuilderV2:
    def __init__(self, agent_id: str, db: AsyncIOMotorDatabase):
        self.agent_id = agent_id
        self.db = db
        self.agent_websites_collection = self.db.agent_websites
        
        # Get absolute path to templates
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = os.path.abspath(
            os.path.join(current_dir, "..", "templates", "agent_site_v2")
        )
        
        # Verify template directory exists
        if not os.path.exists(self.template_dir):
            logger.error(f"Template directory not found: {self.template_dir}")
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
        
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        logger.info(f"Using template directory: {self.template_dir}")

    def _datetimeformat_filter(self, value, format_str='%B %d, %Y %I:%M %p'):
        if not value:
            return ''
        if isinstance(value, datetime):
            return value.strftime(format_str)
        try:
            dt_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt_obj.strftime(format_str)
        except Exception:
            return str(value)

    def _basename_filter(self, path):
        if not path:
            return ''
        return os.path.basename(path)


    async def _get_agent_website_data(self) -> Optional[AgentWebsite]:
        """Fetches the agent's website data from MongoDB."""
        doc = await self.agent_websites_collection.find_one({"_id": self.agent_id})
        if doc:
            try:
                return AgentWebsite(**doc)
            except Exception as e:
                logger.error(f"Error loading AgentWebsite model for '{self.agent_id}': {e}", exc_info=True)
                return None
        return None

    async def _save_agent_website_data(self, agent_website: AgentWebsite):
        """Saves or updates the agent's website data in MongoDB."""
        data_to_save = agent_website.model_dump(by_alias=True, exclude_none=False)
        data_to_save["_id"] = self.agent_id 

        result = await self.agent_websites_collection.update_one(
            {"_id": self.agent_id},
            {"$set": data_to_save},
            upsert=True
        )
        if result.acknowledged:
            logger.info(f"Agent website data for '{self.agent_id}' saved/updated in MongoDB.")
        else:
            logger.error(f"Failed to save/update agent website data for '{self.agent_id}'.")
            raise Exception(f"Failed to save agent website data for {self.agent_id}")

    async def add_post_to_website(self, post: FacebookPostResponse):
        """Adds a new Facebook post to the agent's website data in MongoDB."""
        logger.info(f"Adding new post to website data for agent '{self.agent_id}'. Post ID: {post.post_id}")
        agent_website = await self._get_agent_website_data()

        if not agent_website:
            logger.warning(f"No existing website data found for agent '{self.agent_id}'. Creating a new one.")
            agent_website = AgentWebsite(agent_id=self.agent_id, name=f"{self.agent_id}'s Website")
        
        agent_website.posts.append(post)
        await self._save_agent_website_data(agent_website)
        logger.info(f"Post '{post.post_id}' successfully added to agent '{self.agent_id}'s website data.")

    async def generate_site(self):
        """Generate static site with AI branding"""
        logger.info(f"Building site for {self.agent_id}")
        agent_data = await self._get_agent_website_data()
        
        if not agent_data:
            logger.error(f"No data found for {self.agent_id}")
            raise HTTPException(404, "Agent data not found")
        
        # Use default logo if none provided
        if not agent_data.logo_url:
            agent_data.logo_url = "default_logo.png"
            logger.warning(f"Using default logo for {self.agent_id}")

        template = self.env.get_template("index.html")
        context = {
            "agent": agent_data,
            "posts": [post.model_dump() for post in agent_data.posts],
            "logo_url": f"/generated_images/{agent_data.logo_url}",
            "current_year": datetime.now().year
        }
        
        rendered = template.render(context)
        output_path = os.path.join(self.output_dir, "index.html")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        
        logger.info(f"Site generated at {output_path}")