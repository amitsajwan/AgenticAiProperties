import asyncio
import logging
import os
import json # [ADDED]
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings

# --- Import all necessary routers ---
from api.endpoints.facebook.auth import router as auth_router, clean_expired_tokens
from api.endpoints.facebook.posts import router as posts_router
from api.endpoints.facebook.status import router as status_router
from api.endpoints.facebook.insights import router as insights_router
from api.endpoints.facebook.webhooks import router as webhooks_router
from api.endpoints.bot import router as bot_router
from api.endpoints.agent_website import router as website_router

# Initialize logging 
from logging_config import configure_logging
configure_logging()


logger = logging.getLogger(__name__)
# --- Static Files Configuration ---
IMAGES_DIR = "generated_images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)
    logger.info(f"Created image directory: {IMAGES_DIR}")

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Properties",
    description="Platform for real estate agent branding and content publishing",
    version="1.0.0",
)

# -------------------
# Logging Middleware
# -------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    upgrade = request.headers.get("upgrade", "").lower()
    if upgrade == "websocket":
        logger.info(f"WebSocket handshake origin: {origin!r}")

    logger.info(f"--> {request.method} {request.url}")
    if request.method != "GET" and upgrade != "websocket":
        try:
            body = await request.body()
            # Log only first 500 chars to prevent overly large logs
            logger.info(f"    Body: {body.decode(errors='ignore')[:500]}{'...' if len(body) > 500 else ''}")
        except Exception:
            # Handle cases where body might not be readable (e.g., streaming)
            pass

    response = await call_next(request)
    logger.info(f"<-- {response.status_code} {request.url.path}")
    return response

# -----
# CORS
# -----
# For production, you should revert this to specific origins from settings.CORS_ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # <--- Set to "*" for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Static Files ---
# This allows you to access images via http://localhost:8000/generated_images/image.png
app.mount("/generated_images", StaticFiles(directory=IMAGES_DIR), name="static_images")


# --------------------
# Startup & Shutdown
# --------------------
@app.on_event("startup")
async def on_startup():
    logger.info("Application startup initiated.")
    # Start the background task for cleaning expired OAuth state tokens
    asyncio.create_task(clean_expired_tokens())
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown initiated.")
    logger.info("Application shutdown complete.")

# -------------
# Health Check
# -------------
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ---------------
# Include Routers
# ---------------
# API routers are included with their respective prefixes
app.include_router(auth_router, prefix="/api/facebook/auth", tags=["Facebook Authentication"])
app.include_router(status_router, prefix="/api/facebook/status", tags=["Facebook Status"])
app.include_router(posts_router, prefix="/api/facebook", tags=["Facebook Posts"]) # Note: prefix is /api/facebook, so endpoint is /api/facebook/posts
app.include_router(insights_router, prefix="/api/facebook/insights", tags=["Facebook Insights"])
app.include_router(webhooks_router, prefix="/api/facebook/webhooks", tags=["Facebook Webhooks"])
app.include_router(bot_router, prefix="/api/bot", tags=["AI Bot"])
app.include_router(website_router, prefix="/api/agents", tags=["Agent Websites"])

from api.endpoints.facebook import status as facebook_status_router

app.include_router(facebook_status_router.router, prefix="/api/facebook", tags=["Facebook"])



