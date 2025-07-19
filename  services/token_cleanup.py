import asyncio
from datetime import datetime
from api.endpoints.facebook.auth import state_tokens
import logging

logger = logging.getLogger(__name__)

async def clean_expired_tokens():
    while True:
        try:
            now = datetime.utcnow()
            expired = [
                token for token, data in state_tokens.items()
                if (now - data["created_at"]).total_seconds() > 300
            ]
            for token in expired:
                state_tokens.pop(token, None)
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Token cleanup failed: {str(e)}")
            await asyncio.sleep(60)


