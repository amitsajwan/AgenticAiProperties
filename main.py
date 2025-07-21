import asyncio
import logging
import os
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from core.config import settings
from logging_config import configure_logging

from services.ai.post_workflow import post_graph  # ✅ required for LangGraph streaming

# --- Configure Logging ---
configure_logging()
logger = logging.getLogger(__name__)

# --- Constants for Directories ---
IMAGES_DIR = "generated_images"
AGENT_SITE_V2_DIR = os.path.abspath("agent_sites_v2")

# --- Ensure Directories Exist ---
for path in [IMAGES_DIR, AGENT_SITE_V2_DIR]:
    os.makedirs(path, exist_ok=True)
    logger.info(f"Ensured directory exists: {path}")

# --- FastAPI App ---
app = FastAPI(
    title="Agentic AI Properties",
    description="Platform for real estate agent branding and content publishing",
    version="1.0.0",
)

# -------------------
# Middleware: Logging & CORS
# -------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"--> {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"<-- {response.status_code} {request.url.path}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------
# Mount Static Folder for Generated Images
# ---------------------
app.mount("/generated_images", StaticFiles(directory=IMAGES_DIR), name="static_images")

# -----------------------
# Startup & Shutdown Hooks
# -----------------------
from api.endpoints.facebook.auth import clean_expired_tokens

@app.on_event("startup")
async def on_startup():
    logger.info("Application startup initiated.")
    asyncio.create_task(clean_expired_tokens())
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown complete.")

# ----------------
# API Routers
# ----------------
from api.endpoints.facebook.auth import router as auth_router
from api.endpoints.facebook.facebook import router as facebook_router
from api.endpoints.facebook.insights import router as insights_router
from api.endpoints.facebook.webhooks import router as webhooks_router
from api.endpoints.bot import router as bot_router
from api.endpoints.agent_website import router as website_router

app.include_router(auth_router,     prefix="/api/facebook/auth",     tags=["Facebook Authentication"])
app.include_router(facebook_router, prefix="/api/facebook",          tags=["Facebook"])
app.include_router(insights_router, prefix="/api/facebook/insights", tags=["Facebook Insights"])
app.include_router(webhooks_router, prefix="/api/facebook/webhooks", tags=["Facebook Webhooks"])
app.include_router(bot_router,      prefix="/api/bot",               tags=["AI Bot"])
app.include_router(website_router,  prefix="/api/agents",            tags=["Agent Websites"])

# -------------------------
# WebSocket LangGraph Integration
# -------------------------
@app.websocket("/api/bot/chat")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for client: {client_id}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received input from {client_id}: {data}")

            state = {
                "user_input": data,
                "client_id": client_id,
                "websocket": websocket,
                "brand_suggestions": None,
                "selected_brand": None,
                "visual_prompts": None,
                "image_path": None,
                "location": None,
                "price": None,
                "bedrooms": None,
                "features": [],
                "base_post": None,
                "missing_info": [],
                "post_result": None,
                "db": None,  # you can inject db if needed
            }

            async for step in post_graph.astream(state):
                step_key, updated_state = step
                await websocket.send_text(f"[{step_key}] {updated_state.get('base_post') or updated_state.get('brand_suggestions')}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.exception(f"WebSocket error for {client_id}: {e}", exc_info=True)

# ---------------------------------------------------------------------------------
# CATCH-ALL ROUTE for Agent Websites (Replaces app.mount for better control)
# ---------------------------------------------------------------------------------
@app.get("/{full_path:path}")
async def serve_agent_site(full_path: str):
    if ".." in full_path:
        raise HTTPException(status_code=404, detail="Not Found")

    file_path = os.path.join(AGENT_SITE_V2_DIR, full_path)

    if os.path.isdir(file_path):
        index_path = os.path.join(file_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
    elif os.path.isfile(file_path):
        return FileResponse(file_path)

    logger.warning(f"Static file not found: {file_path}")
    raise HTTPException(status_code=404, detail="Not Found")
