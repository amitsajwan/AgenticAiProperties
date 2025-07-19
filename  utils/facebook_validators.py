from fastapi import HTTPException
from datetime import datetime
from typing import Optional
import re

class FacebookValidators:
    @staticmethod
    def validate_post_text(text: str, max_length: int = 5000):
        if len(text) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Post text exceeds {max_length} characters"
            )
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Post text cannot be empty"
            )

    @staticmethod
    def validate_schedule_time(schedule_time: Optional[datetime]):
        if schedule_time and schedule_time < datetime.now() + timedelta(minutes=10):
            raise HTTPException(
                status_code=400,
                detail="Scheduled time must be at least 10 minutes in future"
            )

    @staticmethod
    def validate_page_id(page_id: str):
        if not re.match(r'^\d+$', page_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid Facebook Page ID format"
            )

    @staticmethod
    def validate_image_urls(urls: list):
        if len(urls) > 4:
            raise HTTPException(
                status_code=400,
                detail="Maximum 4 images allowed per post"
            )
        for url in urls:
            if not url.startswith(('http://', 'https://')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image URL: {url}"
                )

