# services/website_builder_v2.py

import logging
import os
from pathlib import Path
from datetime import datetime

from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.facebook import FacebookPostResponse
from models.agent import AgentWebsite

logger = logging.getLogger(__name__)


class WebsiteBuilderV2:
    def __init__(self, agent_id: str, db: AsyncIOMotorDatabase):
        self.agent_id = agent_id
        self.db = db    
        self.agent_websites_collection = self.db.agent_websites
        

        # 1) Resolve project root and template directory
        here = Path(__file__).parent            # …/services

        project_root = Path(__file__).parent.parent
        self.template_dir = project_root / "templates" / "agent_site_v2"
        
        if not (self.template_dir / "index.html").exists():
            (self.template_dir / "index.html").write_text("<html><body><img src='{{ logo_url }}'></body></html>")


        # 2) Debug: inspect template directory
        if self.template_dir.exists():
            logger.info(f"[BuilderV2] Templates directory found: {self.template_dir}")
            for item in self.template_dir.iterdir():
                logger.info(f"  → {item.name}")
        else:
            logger.error(f"[BuilderV2] Templates directory does NOT exist: {self.template_dir}")

        # 3) If index.html is missing, auto‐generate a minimal fallback
        index_path = self.template_dir / "index.html"
        if not index_path.exists():
            logger.warning(f"[BuilderV2] index.html missing, creating fallback at: {index_path}")
            os.makedirs(self.template_dir, exist_ok=True)
            fallback_html = (
                "<!doctype html>\n"
                "<html><head><meta charset='utf-8'><title>{{ agent.name }}</title></head>\n"
                "<body>\n"
                "  <h1>{{ agent.name }}</h1>\n"
                "  <img src='{{ logo_url }}' alt='Logo'/>\n"
                "  <p>Generated on {{ current_year }}</p>\n"
                "</body></html>"
            )
            index_path.write_text(fallback_html, encoding="utf-8")
            logger.info(f"[BuilderV2] Fallback index.html written.")

        # 4) Initialize Jinja environment
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        logger.info(f"[BuilderV2] Jinja environment initialized with templates at: {self.template_dir}")

        # 5) Prepare output directory for static site
        self.output_dir = project_root / "agent_sites_v2" / self.agent_id
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"[BuilderV2] Static site output directory: {self.output_dir}")

    async def _get_agent_website_data(self) -> AgentWebsite:
        """Load the agent’s website record from MongoDB into a Pydantic model."""
        doc = await self.agent_websites_collection.find_one({"_id": self.agent_id})
        if not doc:
            logger.error(f"[BuilderV2] No MongoDB record for agent: {self.agent_id}")
            return None
        try:
            return AgentWebsite(**doc)
        except Exception as e:
            logger.error(f"[BuilderV2] Pydantic parse error for '{self.agent_id}': {e}", exc_info=True)
            return None

    async def _save_agent_website_data(self, agent_website: AgentWebsite):
        """Persist the AgentWebsite model back to MongoDB."""
        data = agent_website.model_dump(by_alias=True, exclude_none=False)
        data["_id"] = self.agent_id
        result = await self.agent_websites_collection.update_one(
            {"_id": self.agent_id},
            {"$set": data},
            upsert=True
        )
        if not result.acknowledged:
            logger.error(f"[BuilderV2] Failed to save data for '{self.agent_id}'")
            raise Exception(f"Failed to save agent website data for {self.agent_id}")
        logger.info(f"[BuilderV2] MongoDB document saved for '{self.agent_id}'")

    async def add_post_to_website(self, post: FacebookPostResponse):
        """
        Add a newly created FacebookPostResponse to the agent’s website document.
        """
        logger.info(f"[BuilderV2] Appending post {post.post_id} to agent {self.agent_id}")
        agent_data = await self._get_agent_website_data()
        if not agent_data:
            agent_data = AgentWebsite(agent_id=self.agent_id, name=f"{self.agent_id}'s Site")
        agent_data.posts.append(post)
        await self._save_agent_website_data(agent_data)

    async def generate_site(self):
        """
        Render the Jinja2 template to produce index.html under agent_sites_v2/{agent_id}.
        """
        logger.info(f"[BuilderV2] Generating site for agent '{self.agent_id}'")

        agent_data = await self._get_agent_website_data()
        if not agent_data:
            raise HTTPException(404, f"No data found for agent '{self.agent_id}'")

        # If no custom logo, use default
        if not agent_data.logo_url:
            agent_data.logo_url = "default_logo.png"
            logger.warning(f"[BuilderV2] No logo_url set; using default for '{self.agent_id}'")

        # Load template
        try:
            template = self.env.get_template("index.html")
        except Exception as e:
            logger.error(f"[BuilderV2] Failed to load 'index.html' from {self.template_dir}: {e}", exc_info=True)
            raise HTTPException(500, "Template missing: index.html")

        # Build context and render
        context = {
            "agent": agent_data,
            "posts": [p.model_dump() for p in agent_data.posts],
            "logo_url": f"/generated_images/{agent_data.logo_url}",
            "current_year": datetime.now().year
        }
        rendered = template.render(context)

        # Write static HTML
        output_path = self.output_dir / "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        logger.info(f"[BuilderV2] Site written to {output_path}")