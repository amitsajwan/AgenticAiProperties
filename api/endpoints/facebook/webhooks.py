from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import hmac
import hashlib
import logging
import json
from core.config import settings
from services.facebook_webhook_handler import WebhookHandler
from models.facebook import FacebookWebhookPayload
from typing import Dict, Any

router = APIRouter()
logger = logging.getLogger(__name__)
handler = WebhookHandler()

@router.get("")
async def verify_webhook(
    request: Request,
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    """
    Verify Facebook webhook subscription
    
    This endpoint is called by Facebook during webhook setup
    to verify ownership and intent to receive events.
    """
    try:
        # Validate verification token
        if hub_verify_token != settings.FB_WEBHOOK_VERIFY_TOKEN:
            logger.warning(
                f"Invalid verification token received: {hub_verify_token}"
            )
            raise HTTPException(
                status_code=403, 
                detail="Invalid verification token"
            )
            
        # Return challenge to confirm subscription
        return JSONResponse(content=int(hub_challenge))
        
    except Exception as e:
        logger.error(f"Webhook verification failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Webhook verification process failed"
        )

@router.post("")
async def handle_webhook(
    request: Request, 
    background_tasks: BackgroundTasks
):
    """
    Process incoming Facebook webhook events
    
    Handles:
    - Signature verification for security
    - Event parsing and validation
    - Background processing for non-critical tasks
    """
    try:
        # Read raw body for signature validation
        body_bytes = await request.body()
        
        # Verify X-Hub-Signature-256 header
        signature_header = request.headers.get('X-Hub-Signature-256', '')
        if not signature_header:
            logger.warning("Missing X-Hub-Signature-256 header")
            raise HTTPException(
                status_code=403,
                detail="Missing signature header"
            )
            
        # Extract signature value (format: "sha256=<signature>")
        signature = signature_header.split('sha256=')[-1].strip()
        
        # Generate HMAC signature
        calculated_signature = hmac.new(
            settings.FB_APP_SECRET.encode('utf-8'),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, calculated_signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=403,
                detail="Invalid signature"
            )
        
        # Parse JSON payload
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload"
            )
        
        # Validate payload structure
        try:
            validated_payload = FacebookWebhookPayload(**payload)
        except Exception as e:
            logger.error(f"Payload validation failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Invalid payload structure"
            )
        
        # Process event in background to avoid blocking
        background_tasks.add_task(
            handler.process_event, 
            validated_payload.dict()
        )
        
        return {"status": "ok"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(
            f"Webhook processing failed: {str(e)}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Webhook processing error"
        )

