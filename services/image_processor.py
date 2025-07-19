import aiofiles
import os
import logging
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from pathlib import Path
from typing import List
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class PropertyImageProcessor:
    def __init__(self):
        self.allowed_types = ["image/jpeg", "image/png"]
        self.max_size = 10 * 1024 * 1024  # 10MB

    async def validate_image_file(
        self, 
        upload: UploadFile, 
        allowed_types: List[str], 
        max_size: int
    ):
        """Validate image file type and size"""
        if upload.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        if upload.size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size/1024/1024}MB"
            )
    
    async def validate_image_integrity(self, file_path: str):
        """Verify the image is valid and not corrupted"""
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verify without loading
        except (UnidentifiedImageError, Exception) as e:
            os.unlink(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
    
    async def create_resized_copy(
        self, 
        original_path: str, 
        max_dimensions: tuple[int, int]
    ) -> str:
        """Create resized copy if image exceeds max dimensions"""
        with Image.open(original_path) as img:
            if img.width <= max_dimensions[0] and img.height <= max_dimensions[1]:
                return original_path
                
            # Create resized copy
            img.thumbnail(max_dimensions)
            new_path = f"{original_path}_resized{Path(original_path).suffix}"
            img.save(new_path, quality=85)
            return new_path

