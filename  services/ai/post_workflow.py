import os
import shutil
import logging
from typing import TypedDict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import asyncio

from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from services.social_media.facebook_manager import create_facebook_post
from core.config import settings

logger = logging.getLogger(__name__)

# Initialize your LLM
try:
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama3-70b-8192",
        temperature=0.4
    )
    logger.info("ChatGroq LLM initialized successfully.")
except Exception as e:
    logger.error(f"ChatGroq initialization failed: {e}", exc_info=True)
    llm = None # Ensure llm is None if initialization fails

# Define the state schema
class BrandingPostState(TypedDict):
    user_input: Optional[str]
    brand_suggestions: Optional[str] # Will contain all 3 initial suggestions
    selected_brand: Optional[str]   # NEW: To store the user's chosen brand
    visual_prompts: Optional[str]
    image_path: Optional[str]
    location: Optional[str]
    price: Optional[str]
    bedrooms: Optional[str]
    features: List[str]
    base_post: Optional[str]
    missing_info: List[str]
    post_result: Optional[dict]
    websocket: Optional[object]
    client_id: Optional[str]
    db: Optional[object] # Add db to state if nodes need it
    # New field to store the decision for routing
    next_step_after_branding_decision: Optional[str]

# Node: generate brand suggestions
def create_branding_node(state: BrandingPostState) -> dict:
    if not llm:
        logger.error("LLM not initialized, cannot create branding suggestions.")
        return {"brand_suggestions": "Error: LLM not available."}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You’re an expert real estate marketer. Generate 3 distinct brand name + slogan pairs, each on a new line. Format as 'Pair 1: Brand Name - Slogan\\nPair 2: Brand Name - Slogan'"), # Improved prompt for parsing
        ("user", "Idea: {user_input}")
    ])
    chain = prompt | llm | StrOutputParser()
    out = chain.invoke({"user_input": state["user_input"]})
    logger.info(f"Generated brand suggestions: {out[:100]}...")
    return {"brand_suggestions": out.strip()}

# Node: create a visual prompt
def create_visuals_node(state: BrandingPostState) -> dict:
    if not llm:
        logger.error("LLM not initialized, cannot create visual prompts.")
        return {"visual_prompts": "Error: LLM not available."}

    # Use selected_brand if available, otherwise fallback to brand_suggestions (shouldn't happen in multi-step)
    brand_context = state.get("selected_brand") or state.get("brand_suggestions")
    if not brand_context:
        logger.warning("No brand context available for visual prompt generation.")
        return {"visual_prompts": "No brand context."}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You’re a creative director. Write a photorealistic image prompt. Focus on the core branding and property style."),
        ("user", "Branding to inspire visuals: {brand_context}")
    ])
    chain = prompt | llm | StrOutputParser()
    out = chain.invoke({"brand_context": brand_context})
    logger.info(f"Generated visual prompts: {out[:100]}...")
    return {"visual_prompts": out.strip()}

# Node: simulate image generation (consider replacing with actual Stability AI call if available)
def generate_image_node(state: BrandingPostState) -> dict:
    image_dir = "generated_images"
    os.makedirs(image_dir, exist_ok=True)
    placeholder = "placeholder.png"

    # Create placeholder image if it doesn't exist
    if not os.path.exists(placeholder):
        img = Image.new("RGB", (1024, 1024), (200, 200, 200))
        d = ImageDraw.Draw(img)
        try:
            # Use a robust font loading strategy or ensure font exists
            font_path = "arial.ttf" # Assuming arial.ttf is in the same directory or accessible
            if not os.path.exists(font_path):
                 # Fallback to default if arial.ttf is not found
                font = ImageFont.load_default()
                logger.warning(f"Font '{font_path}' not found, using default font.")
            else:
                font = ImageFont.truetype(font_path, 40)

        except Exception as e:
            font = ImageFont.load_default()
            logger.error(f"Error loading font, using default: {e}", exc_info=True)
        d.text((10, 10), "Placeholder Image", fill=(0, 0, 0), font=font)
        img.save(placeholder)
        logger.info(f"Created new placeholder image at {placeholder}")

    out_path = os.path.join(image_dir, f"{state.get('client_id', 'unknown_agent')}_img.png")
    shutil.copy(placeholder, out_path)
    logger.info(f"Generated placeholder image at {out_path}")
    return {"image_path": out_path}

# Node: check for required property info
def check_requirements_node(state: BrandingPostState) -> dict:
    missing = []
    # Using .get() with a default value prevents KeyError if a key is truly absent
    for key in ("location", "price", "bedrooms", "features"):
        if not state.get(key):
            missing.append(key)
    logger.info(f"Missing info: {missing}")
    return {"missing_info": missing}

# Node: generate the Facebook post copy
def generate_post_node(state: BrandingPostState) -> dict:
    if not llm:
        logger.error("LLM not initialized, cannot generate post copy.")
        return {"base_post": "Error: LLM not available."}

    # Use selected_brand if available, otherwise fallback
    brand_context = state.get("selected_brand") or state.get("brand_suggestions")
    if not brand_context:
        logger.warning("No brand context available for post generation.")
        return {"base_post": "No brand context."}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You’re a world-class real estate copywriter. Write a Facebook post with emojis & CTA."),
        ("user",
         "Property at {location}, price {price}, {bedrooms} beds, features: {features}. "
         "Use branding: {brand_context}") # Use brand_context here
    ])
    chain = prompt | llm | StrOutputParser()
    args = {
        "location": state.get("location", "an undisclosed location"), # Use .get with defaults
        "price": state.get("price", "an undisclosed price"),
        "bedrooms": state.get("bedrooms", "an undisclosed number of"),
        "features": ", ".join(state.get("features", ["no specific features"])),
        "brand_context": brand_context, # Pass the selected/generated brand
    }
    out = chain.invoke(args)
    logger.info(f"Generated post copy: {out[:100]}...")
    return {"base_post": out.strip()}

# Node: post to Facebook via your manager
async def post_to_facebook_node(state: BrandingPostState) -> dict:
    caption = state.get("base_post")
    image_path = state.get("image_path")
    agent_id = state.get("client_id")
    db_session = state.get("db") # Access db from the state if passed

    if not caption or not agent_id:
        logger.error("Cannot post to Facebook: Missing caption or agent ID.")
        return {"post_result": {"status": "failed", "message": "Missing required data for Facebook post."}}

    try:
        fb_resp = await create_facebook_post(
            agent_id=agent_id,
            caption=caption,
            images=[image_path] if image_path else [],
            db=db_session # Pass the db session here
        )
        logger.info(f"Posted to Facebook, got: {fb_resp}")
        return {"post_result": fb_resp}
    except Exception as e:
        logger.error(f"Failed to post to Facebook from graph node: {e}", exc_info=True)
        return {"post_result": {"status": "failed", "message": f"Facebook posting error: {e}"}}


# NEW NODE: Decision node for branding. It MUST return a dict.
def branding_decision_node(state: BrandingPostState) -> dict:
    """
    Determines whether to proceed to create visuals (if brand selected)
    or generate branding suggestions (if no brand selected).
    Returns a dict that sets 'next_step_after_branding_decision' in the state.
    """
    if state.get("selected_brand"):
        logger.info("Brand selected, setting next step to 'create_visuals'.")
        return {"next_step_after_branding_decision": "create_visuals"}
    else:
        logger.info("No brand selected, setting next step to 'create_branding'.")
        return {"next_step_after_branding_decision": "create_branding"}

# NEW ROUTING FUNCTION: This function will be called by conditional_edges
# to read the decision from the state (set by branding_decision_node).
def route_after_branding(state: BrandingPostState) -> str:
    """Reads the 'next_step_after_branding_decision' from state to route."""
    return state.get("next_step_after_branding_decision", "create_branding")


# Decision: all info present?
def decide_after_requirements(state: BrandingPostState) -> str:
    # Ensure missing_info is a list to prevent errors
    if not state.get("missing_info"):
        logger.info("All property info present, proceeding to generate post.")
        return "generate_post"
    logger.info("Missing property info, pausing for input.")
    return "pause_for_input"

# Build and compile the graph
def build_post_graph():
    if not llm:
        logger.error("LLM is None, graph cannot be compiled fully.")

    g = StateGraph(BrandingPostState)

    # Add nodes
    g.add_node("branding_decision_node", branding_decision_node) # NEW: Add the decision node
    g.add_node("create_branding",     create_branding_node)
    g.add_node("create_visuals",      create_visuals_node)
    g.add_node("generate_image",      generate_image_node)
    g.add_node("check_requirements",  check_requirements_node)
    g.add_node("generate_post",       generate_post_node)
    g.add_node("post_to_facebook",    post_to_facebook_node)
    g.add_node("pause_for_input",     lambda s: {})

    # Set entry point to the new decision node
    g.set_entry_point("branding_decision_node")

    # Conditional edges from the branding_decision_node
    g.add_conditional_edges(
        "branding_decision_node", # Source node is the decision node
        route_after_branding,     # This function reads the decision from state
        {
            "create_branding": "create_branding",
            "create_visuals": "create_visuals"
        }
    )

    # Standard flow after branding (either generated or selected)
    g.add_edge("create_branding", "create_visuals") # After generating brands, proceed to visuals
    g.add_edge("create_visuals",  "generate_image")
    g.add_edge("generate_image",  "check_requirements")

    g.add_conditional_edges(
        "check_requirements",
        decide_after_requirements,
        {"generate_post":"generate_post", "pause_for_input":"pause_for_input"}
    )
    g.add_edge("pause_for_input","generate_post") # After pause (e.g., getting missing info), proceed to generate post
    g.add_edge("generate_post","post_to_facebook")
    g.add_edge("post_to_facebook", END)

    logger.info("LangGraph post_graph compiled.")
    return g.compile()

# Instantiate once
try:
    post_graph = build_post_graph()
except RuntimeError as e:
    logger.critical(f"Failed to build post_graph: {e}")
    post_graph = None # Ensure it's None if compilation fails

