import os
import shutil
import logging
import httpx
import base64
from typing import TypedDict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import asyncio

from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from services.social_media.facebook_manager import create_facebook_post
from models.facebook import FacebookPostResponse, PostStatus
from core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# -------------------------------
# LLM Initialization
# -------------------------------
try:
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama3-70b-8192",
        temperature=0.4
    )
    logger.info("ChatGroq LLM initialized successfully.")
except Exception as e:
    logger.error(f"ChatGroq initialization failed: {e}", exc_info=True)
    llm = None


async def generate_image_with_stability(prompt: str) -> bytes:
    api_key = settings.STABILITY_API_KEY
    url = f"https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    json_payload = {
        "text_prompts": [{"text": prompt, "weight": 1.0}],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=json_payload)
        if resp.status_code != 200:
            raise Exception(f"Stability API request failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        art = data.get("artifacts")
        if not art or not art[0].get("base64"):
            raise Exception("No image artifacts in response")
        return base64.b64decode(art[0]["base64"])


async def generate_agent_logo(agent_id: str, logo_prompt: str, db: AsyncIOMotorDatabase) -> str:
    """
    Generate a logo for the agent, writing a PNG to generated_images/<agent_id>_logo.png
    Falls back to a simple placeholder if AI calls fail or if prompt is empty.
    """
    logo_dir = "generated_images"
    os.makedirs(logo_dir, exist_ok=True)
    logo_filename = f"{agent_id}_logo.png"
    agent_logo_path = os.path.join(logo_dir, logo_filename)

    # 1) Build the AI-crafted prompt
    if llm:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You're a creative branding expert. Produce a concise vector‐art logo prompt."),
            ("user", "Brand concept: {logo_prompt_input}")
        ])
        ai_logo_prompt = await (prompt_template | llm | StrOutputParser()).ainvoke({
            "logo_prompt_input": logo_prompt
        })
        logger.info(f"[Logo] Raw AI prompt length: {len(ai_logo_prompt)}\n  >>> {ai_logo_prompt[:80]}...")
    else:
        ai_logo_prompt = f"Modern real estate logo: {logo_prompt}"
        logger.warning("[Logo] LLM unavailable, using generic fallback prompt.")

    # 2) Clean & truncate the prompt to meet Stability bounds
    clean = " ".join(ai_logo_prompt.splitlines()).strip()
    if not clean:
        logger.error("[Logo] Cleaned prompt is empty—skipping Stability call.")
    truncated = clean[:2000]
    logger.info(f"[Logo] Using final prompt ({len(truncated)} chars): {truncated[:80]}...")

    # 3) Try Stability; on failure, use placeholder
    try:
        if clean:
            image_bytes = await generate_image_with_stability(truncated)
            with open(agent_logo_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"[Logo] AI logo generated at: {agent_logo_path}")
        else:
            raise Exception("Empty prompt—skipping AI image generation")
    except Exception as e:
        logger.error(f"[Logo] AI generation failed: {e}. Using placeholder", exc_info=True)
        # Placeholder generation
        img = Image.new("RGB", (512, 512), (30, 60, 90))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
        text = (logo_prompt[:3] or agent_id[:3]).upper()
        draw.text((180, 220), text, fill=(255, 255, 255), font=font)
        img.save(agent_logo_path)
        logger.info(f"[Logo] Placeholder logo saved at: {agent_logo_path}")

    return logo_filename

# -------------------------------
# State Definition (for LangGraph)
# -------------------------------
class BrandingPostState(TypedDict):
    user_input: Optional[str]
    brand_suggestions: Optional[str]
    selected_brand: Optional[str]
    visual_prompts: Optional[str]
    image_path: Optional[str]
    location: Optional[str]
    price: Optional[str]
    bedrooms: Optional[str]
    features: List[str]
    base_post: Optional[str]
    missing_info: List[str]
    post_result: Optional[FacebookPostResponse] 
    websocket: Optional[object]
    client_id: Optional[str]
    db: Optional[object]
    next_step_after_branding_decision: Optional[str]
    logo_prompt: Optional[str]
    logo_url: Optional[str]


# -------------------------------
# Node Functions (for LangGraph)
# -------------------------------
def create_branding_node(state: BrandingPostState) -> dict:
    if not llm:
        logger.error("LLM not initialized.")
        return {"brand_suggestions": "Error: LLM unavailable."}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You’re an expert real estate marketer. Generate 3 distinct brand name + slogan pairs. Format each line as 'Brand - Slogan'"),
        ("user", "Idea: {user_input}")
    ])
    chain = prompt | llm | StrOutputParser()
    out = chain.invoke({"user_input": state.get("user_input", "")})
    logger.info(f"[Branding] Suggestions: {out[:100]}...")
    return {"brand_suggestions": out.strip()}


async def generate_logo_prompt_node(state: BrandingPostState) -> dict:
    # This node is part of the LangGraph flow, but the actual image generation
    # is now handled by the standalone generate_agent_logo function.
    # This node will just set the logo_prompt based on selected_brand.
    brand = state.get("selected_brand", "Real Estate Co.")
    logo_prompt_input = f"Logo for {brand}"
    logger.info(f"[Logo Node] Setting logo prompt: {logo_prompt_input}")
    return {"logo_prompt": logo_prompt_input}


async def generate_logo_image_node(state: BrandingPostState) -> dict:
    # This node now calls the standalone function
    agent_id = state.get("client_id")
    logo_prompt = state.get("logo_prompt")
    db_conn = state.get("db") # Ensure db is passed from the graph state

    if not agent_id or not logo_prompt or not db_conn:
        logger.error("[Logo Node] Missing agent_id, logo_prompt, or db for logo generation.")
        return {"logo_url": None} # Indicate failure

    try:
        logo_filename = await generate_agent_logo(agent_id, logo_prompt, db_conn)
        return {"logo_url": logo_filename}
    except Exception as e:
        logger.error(f"[Logo Node] Error generating logo image: {e}", exc_info=True)
        return {"logo_url": None}


def create_visuals_node(state: BrandingPostState) -> dict:
    if not llm:
        logger.error("LLM not initialized.")
        return {"visual_prompts": "Error: LLM unavailable."}

    brand_context = state.get("selected_brand") or state.get("brand_suggestions")
    if not brand_context:
        logger.warning("[Visuals] No brand context.")
        return {"visual_prompts": "No brand context."}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You’re a creative director. Write a photorealistic image prompt for a real estate listing."),
        ("user", "Brand inspiration: {brand_context}")
    ])
    chain = prompt | llm | StrOutputParser()
    out = chain.invoke({"brand_context": brand_context})
    logger.info(f"[Visuals] Prompt: {out[:100]}...")
    return {"visual_prompts": out.strip()}


def generate_image_node(state: BrandingPostState) -> dict:
    image_dir = "generated_images"
    os.makedirs(image_dir, exist_ok=True)
    placeholder = "placeholder_post_image.png"

    if not os.path.exists(placeholder):
        img = Image.new("RGB", (1024, 1024), (200, 200, 200))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except Exception:
            font = ImageFont.load_default()
        draw.text((10, 10), "Placeholder Image", fill=(0, 0, 0), font=font)
        img.save(placeholder)
        logger.info("[Image] Placeholder created.")

    image_filename = f"{state.get('client_id', 'agent')}_post_image.png"
    image_path = os.path.join(image_dir, image_filename)
    shutil.copy(placeholder, image_path)
    return {"image_path": image_filename}


def check_requirements_node(state: BrandingPostState) -> dict:
    required = ["location", "price", "bedrooms", "features"]
    missing = [key for key in required if not state.get(key)]
    logger.info(f"[Check] Missing: {missing}")
    return {"missing_info": missing}


def generate_post_node(state: BrandingPostState) -> dict:
    if not llm:
        return {"base_post": "Error: LLM unavailable."}

    brand = state.get("selected_brand") or state.get("brand_suggestions", "")
    args = {
        "location": state.get("location", "undisclosed"),
        "price": state.get("price", "undisclosed"),
        "bedrooms": state.get("bedrooms", "undisclosed"),
        "features": ", ".join(state.get("features", ["none listed"])),
        "brand_context": brand
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You’re a world-class real estate copywriter. Write a Facebook post with emojis and a clear CTA."),
        ("user", "Property at {location}, price {price}, {bedrooms} beds. Features: {features}. Branding: {brand_context}")
    ])
    chain = prompt | llm | StrOutputParser()
    out = chain.invoke(args)
    logger.info(f"[Post] Caption: {out[:100]}...")
    return {"base_post": out.strip()}


async def post_to_facebook_node(state: BrandingPostState) -> dict:
    agent_id = state.get("client_id")
    caption = state.get("base_post")
    image_path_from_state = state.get("image_path") # This is now just the filename
    db_conn = state.get("db")

    # Construct full image URL if image_path exists for Facebook upload
    full_image_url = f"/generated_images/{image_path_from_state}" if image_path_from_state else None
    
    post_id = "N/A"
    post_url = None
    status = PostStatus.FAILED
    error_message = None

    try:
        # Pass the full image URL to create_facebook_post
        fb_resp = await create_facebook_post(
            agent_id=agent_id,
            caption=caption,
            images=[full_image_url] if full_image_url else [], # Pass the full URL
            db=db_conn
        )
        if isinstance(fb_resp, FacebookPostResponse):
            post_id = fb_resp.post_id
            post_url = fb_resp.url
            status = fb_resp.status
            error_message = fb_resp.error
            logger.info(f"[Facebook] Post created successfully: {post_id}")
        else:
            error_message = f"Unexpected response from Facebook post creation: {fb_resp}"
            logger.error(f"[Facebook] {error_message}")

    except Exception as e:
        error_message = str(e)
        logger.error(f"[Facebook] Error creating post: {error_message}", exc_info=True)
    
    return_post_result = FacebookPostResponse(
        agent_id=agent_id,
        post_id=post_id,
        message=caption,
        url=post_url,
        status=status,
        error=error_message,
        ai_generated=True,
        image_path=image_path_from_state # Store just the filename in the DB
    )
    return {"post_result": return_post_result}


# -------------------------------
# Routing Logic
# -------------------------------
def branding_decision_node(state: BrandingPostState) -> dict:
    next_step = "generate_logo_prompt" if state.get("selected_brand") else "create_branding"
    logger.info(f"[Decision] Next: {next_step}")
    return {"next_step_after_branding_decision": next_step}


def route_after_branding(state: BrandingPostState) -> str:
    return state.get("next_step_after_branding_decision", "create_branding")


def decide_after_requirements(state: BrandingPostState) -> str:
    return "generate_post" if not state.get("missing_info") else "pause_for_input"


# -------------------------------
# Graph Definition
# -------------------------------
def build_post_graph():
    g = StateGraph(BrandingPostState)

    g.set_entry_point("branding_decision_node")
    g.add_node("branding_decision_node", branding_decision_node)
    g.add_node("create_branding", create_branding_node)
    g.add_node("generate_logo_prompt", generate_logo_prompt_node)
    g.add_node("generate_logo_image", generate_logo_image_node)
    g.add_node("create_visuals", create_visuals_node)
    g.add_node("generate_image", generate_image_node)
    g.add_node("check_requirements", check_requirements_node)
    g.add_node("generate_post", generate_post_node)
    g.add_node("post_to_facebook", post_to_facebook_node)
    g.add_node("pause_for_input", lambda s: {}) 

    # Conditional transitions from branding decision
    g.add_conditional_edges(
        "branding_decision_node",
        route_after_branding,
        {
            "create_branding": "create_branding",
            "generate_logo_prompt": "generate_logo_prompt"
        }
    )

    # Logo flow
    g.add_edge("create_branding", "generate_logo_prompt")
    g.add_edge("generate_logo_prompt", "generate_logo_image")
    g.add_edge("generate_logo_image", "create_visuals")

    # Visual flow
    g.add_edge("create_visuals", "generate_image")
    g.add_edge("generate_image", "check_requirements")

    # Info check & routing
    g.add_conditional_edges(
        "check_requirements",
        decide_after_requirements,
        {
            "generate_post": "generate_post",
            "pause_for_input": "pause_for_input"
        }
    )

    g.add_edge("pause_for_input", "generate_post")
    g.add_edge("generate_post", "post_to_facebook")
    g.add_edge("post_to_facebook", END)

    logger.info("LangGraph post_graph compiled.")
    return g.compile()


# Initialize graph safely
try:
    post_graph = build_post_graph()
except RuntimeError as e:
    logger.critical(f"Failed to build post_graph: {e}")
    post_graph = None

