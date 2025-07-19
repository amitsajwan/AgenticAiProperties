# models/facebook.py

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class PostStatus(str, Enum):
    DRAFT     = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED    = "failed"
    DELETED   = "deleted"


class TokenStatus(str, Enum):
    ACTIVE   = "active"
    EXPIRED  = "expired"
    REVOKED  = "revoked"
    LIMITED  = "limited"


class FacebookPostBase(BaseModel):
    """Base model for Facebook posts"""
    post_id: str = Field(..., description="Facebook's unique post identifier")
    message: str = Field(..., max_length=5000, description="Post content text")
    url:     str = Field(..., description="Permalink to the post on Facebook")


class FacebookPostCreate(FacebookPostBase):
    """Model for creating new posts"""
    agent_id:       str          = Field(..., description="Associated agent ID")
    images:         List[str]    = Field(
        default_factory=list,
        max_items=4,
        description="List of image URLs (max 4)"
    )
    scheduled_time: Optional[datetime] = Field(
        None,
        description="When to publish (null for immediate)"
    )


class FacebookPostResponse(FacebookPostBase):
    """Complete post response model"""
    agent_id:       str
    created_at:     datetime      = Field(default_factory=datetime.utcnow)
    updated_at:     Optional[datetime] = None
    status:         PostStatus    = Field(PostStatus.PUBLISHED)
    engagement:     Optional[Dict[str, int]] = Field(
        None,
        description="Likes, comments, shares counts"
    )
    error:          Optional[str] = Field(
        None,
        description="Error details if status=failed"
    )
    scheduled_time: Optional[datetime] = None
    ai_generated:   bool          = Field(False)

    @validator("engagement")
    def validate_engagement(cls, v):
        if v:
            for metric in ("likes", "comments", "shares", "impressions"):
                if metric in v and not isinstance(v[metric], int):
                    raise ValueError(f"{metric} must be an integer")
        return v


class FacebookTokenRecord(BaseModel):
    """Encrypted token storage model"""
    access_token:   str          = Field(..., description="Encrypted access token")
    expires_at:     datetime     = Field(..., description="When the token becomes invalid")
    status:         TokenStatus  = Field(TokenStatus.ACTIVE, description="Current token validity")
    scopes:         List[str]    = Field(default_factory=list, description="Granted permissions")
    last_refreshed: datetime     = Field(default_factory=datetime.utcnow,
                                         description="When token was last renewed")


class FacebookPage(BaseModel):
    """Connected Facebook page model"""
    page_id:      str               = Field(..., description="Facebook Page ID")
    name:         str               = Field(..., description="Display name of the Page")
    access_token: str               = Field(..., description="Encrypted Page access token")
    category:     Optional[str]     = Field(None, description="Facebook Page category")
    connected_at: datetime          = Field(default_factory=datetime.utcnow,
                                            description="When connection was established")
    followers:    Optional[int]     = Field(None, description="Current follower count")


class FacebookPostUpdate(BaseModel):
    """Model for post updates"""
    status:     Optional[PostStatus]     = None
    engagement: Optional[Dict[str, int]] = None
    error:      Optional[str]            = Field(
        None,
        max_length=1000,
        description="Failure details"
    )


class PropertyDetails(BaseModel):
    """Real estate property details model"""
    title:           str            = Field(..., max_length=100, description="Property title/headline")
    description:     str            = Field(..., max_length=4000, description="Detailed property description")
    location:        str            = Field(..., max_length=200,  description="Full property address")
    bedrooms:        int            = Field(..., ge=0, le=20,       description="Number of bedrooms")
    bathrooms:       float          = Field(..., ge=0.5, le=20,     description="Number of bathrooms")
    price:           float          = Field(..., gt=0,              description="Listing price")
    amenities:       List[str]      = Field(default_factory=list,   description="List of amenities")
    property_type:   str            = Field("residential",         description="Type of property")
    square_footage:  Optional[int]  = Field(None, gt=0,             description="Size in square feet")

    @validator("price")
    def round_price(cls, v):
        return round(v, 2)


class FacebookPostAnalytics(BaseModel):
    """Post performance analytics model"""
    post_id:      str
    agent_id:     str
    period_start: datetime
    period_end:   datetime
    reach:        int     = Field(..., ge=0)
    engagements:  int     = Field(..., ge=0)
    clicks:       int     = Field(..., ge=0)
    ctr:          float   = Field(..., ge=0, le=100)
    demographics: Dict[str, float] = Field(
        default_factory=dict,
        description="Age/gender breakdown"
    )


class FacebookWebhookPayload(BaseModel):
    """Model for Facebook webhook notifications"""
    object: str
    entry:  List[Dict[str, Any]]


class FacebookPostSchedule(BaseModel):
    """Scheduled post model (if needed)"""
    post_time:       datetime         = Field(..., description="When to publish")
    property_details: PropertyDetails = Field(..., description="Details of the property")


class PostResult(BaseModel):
    """Utility result model for publishing flows"""
    post_id:       str
    message:       str
    url:           str
    scheduled_time: Optional[datetime] = None

