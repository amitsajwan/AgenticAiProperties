# core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List # Import List

class Settings(BaseSettings):
    GROQ_API_KEY: str
    PROJECT_NAME: str = "Real Estate Social Media Manager"
    API_V1_STR: str = "/api"

    FB_APP_ID: str
    FB_APP_SECRET: str
    FB_REDIRECT_URI: str
    FB_PAGE_ID: Optional[str] = None
    FB_API_VERSION: str = "v19.0"
    FB_ENCRYPTION_KEY: str

    MONGO_URI: str
    MONGO_DB_NAME: str = "property_agents"

    STABILITY_API_KEY: str
    OPENAI_API_KEY: str

    # CHANGE THIS LINE:
    CORS_ALLOWED_ORIGINS: List[str] = ["*"]


    FRONTEND_URL: str = Field("http://localhost:3000", env="FRONTEND_URL")


    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

