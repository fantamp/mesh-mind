import os
from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: Literal["dev", "prod"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Paths
    DB_PATH: str = "data/db/mesh_mind.db"
    CHROMA_PATH: str = "data/vector_store"
    MEDIA_PATH: str = "data/media"
    
    # API Keys
    GOOGLE_API_KEY: str
    
    # Models
    # GEMINI_MODEL_FAST: str = "gemini-2.5-flash"
    # GEMINI_MODEL_SMART: str = "gemini-2.5-pro"
    GEMINI_MODEL_FAST: str = "gemini-2.0-flash" # больше лимиты, ок для тестов
    GEMINI_MODEL_SMART: str = "gemini-2.0-flash" # больше лимиты, ок для тестов
    
    
    # Company
    COMPANY_DOMAINS: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()
