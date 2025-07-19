 

import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
 
from api.endpoints.facebook.auth import router as auth_router, clean_expired_tokens


from api.endpoints.facebook.posts    import router as posts_router
from api.endpoints.facebook.insights import router as insights_router
from api.endpoints.facebook.webhooks import router as webhooks_router
 
from api.endpoints.bot               import router as bot_router
 
from api.endpoints.agent_website     import router as website_router
 
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Properties",
    description="Platform for real estate agent branding and content publishing",
    version="1.0.0"
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
            logger.info(f"    Body: {body.decode(errors='ignore')}")
        except Exception:
            pass

    response = await call_next(request)
    logger.info(f"<-- {response.status_code} {request.url.path}")
    return response

# -----
# CORS
# -----
origins = settings.CORS_ALLOWED_ORIGINS
if isinstance(origins, str):
    origins = [o.strip() for o in origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,   # disable for WS if you don’t need cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# Startup & Shutdown
# --------------------
@app.on_event("startup")
async def on_startup():
    logger.info("Application startup initiated.")
    # kick off the background state-token cleanup
    asyncio.create_task(clean_expired_tokens())
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown initiated.")
    # any teardown logic here
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
app.include_router(
    auth_router,
    prefix="/api/facebook/auth",
    tags=["Facebook Authentication"],
)

app.include_router(
    posts_router,
    prefix="/api/facebook/posts",
    tags=["Facebook Posts"],
)

app.include_router(
    insights_router,
    prefix="/api/facebook/insights",
    tags=["Facebook Insights"],
)

app.include_router(
    webhooks_router,
    prefix="/api/facebook/webhooks",
    tags=["Facebook Webhooks"],
)

app.include_router(
    bot_router,
    prefix="/api/bot",
    tags=["AI Bot"],
)

app.include_router(
    website_router,
    prefix="/api/agents",
    tags=["Agent Websites"],
)


