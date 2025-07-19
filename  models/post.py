from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"

class PropertyDetails(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=4000)
    location: str = Field(..., max_length=200)
    bedrooms: int = Field(..., ge=0, le=20)
    bathrooms: float = Field(..., ge=0.5, le=20)
    price: float = Field(..., gt=0)
    amenities: List[str] = Field(default_factory=list)
    property_type: str = Field("residential")
    square_footage: Optional[int] = Field(None, gt=0)

    @field_validator('price')
    def round_price(cls, v): return round(v, 2)

class FacebookPost(BaseModel):
    agent_id: str
    post_id: str
    content: str
    images: List[str] = []
    status: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_updated: Optional[datetime] = None
    engagement: Optional[Dict[str, int]] = None
    error: Optional[str] = None

class FacebookPostResponse(BaseModel):
    post_id: str
    message: str
    url: str
    images: List[str]
    scheduled: Optional[bool] = False
    scheduled_time: Optional[datetime] = None
    ai_generated: Optional[bool] = False

class FacebookPostUpdate(BaseModel):
    status: Optional[PostStatus] = None
    engagement: Optional[Dict[str, int]] = None
    error: Optional[str] = None


