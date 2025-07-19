from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from enum import Enum

class TokenStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LIMITED = "limited"

class FacebookTokenRecord(BaseModel):
    access_token: str
    expires_at: datetime
    status: TokenStatus = TokenStatus.ACTIVE
    scopes: List[str] = Field(default_factory=list)
    last_refreshed: datetime = Field(default_factory=datetime.utcnow)


