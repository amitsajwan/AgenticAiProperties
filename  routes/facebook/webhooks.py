from fastapi import APIRouter, Request, Header, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime
import hashlib
import hmac
import logging
from db.session import get_db
from core.config import settings

router = APIRouter()
logger = logging.getLogger("facebook_webhook")
FB_APP_SECRET = settings.FB_APP_SECRET  # Uses env-configured secret

def verify_signature(payload: bytes, received_signature: str) -> bool:
    expected = hmac.new(
        key=FB_APP_SECRET.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received_signature.split("sha256=")[-1])

@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    db: AsyncIOMotorCollection = Depends(get_db)
):
    body = await request.body()

    if not x_hub_signature_256 or not verify_signature(body, x_hub_signature_256):
        logger.warning("[Webhook] Signature mismatch — possible spoof")
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    logger.info(f"[Webhook] Received: {payload.get('object')} @ {datetime.utcnow()}")

    try:
        await db.insert_one({
            "object": payload.get("object"),
            "entry": payload.get("entry", []),
            "received_at": datetime.utcnow()
        })
        logger.info("[Webhook] Event saved successfully")
    except Exception as e:
        logger.error(f"[Webhook] Failed to save event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook persistence error")

    return { "status": "received" }

