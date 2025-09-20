"""
Application settings and configuration management
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "CV Analyzer AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/cvanalyzer"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API settings
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx"]
    UPLOAD_DIR: str = "uploads"
    
    # ML Model settings
    SPACY_MODEL: str = "en_core_web_sm"
    MODEL_CACHE_DIR: str = "models"
    
    # Redis settings (for caching and rate limiting)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Rate limiting
    REQUESTS_PER_MINUTE: int = 100
    REQUESTS_PER_HOUR: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings