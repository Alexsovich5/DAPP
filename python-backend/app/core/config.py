"""
Configuration settings for the Dinner First Dating Platform
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/dinner_first")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost:5001,http://127.0.0.1:4200,http://127.0.0.1:5001"
    
    # AI Matching settings
    AI_MATCHING_ENABLED: bool = True
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.6
    COMPATIBILITY_THRESHOLD: float = 0.7
    
    # Analytics settings
    CLICKHOUSE_URL: str = os.getenv("CLICKHOUSE_URL", "http://localhost:8123")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Feature flags
    ENABLE_SOUL_CONNECTIONS: bool = True
    ENABLE_PHOTO_REVEAL: bool = True
    ENABLE_ANALYTICS: bool = True
    
    # File storage
    UPLOAD_PATH: str = "uploads/"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# Global settings instance
settings = Settings()