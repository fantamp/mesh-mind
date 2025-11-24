import os
from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: Literal["dev", "prod"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"
    
    # Paths
    # Paths
    # Determine project root (2 levels up from this file: ai_core/common/config.py -> ai_core/common -> ai_core -> root)
    # Wait, config.py is in ai_core/common.
    # dirname = ai_core/common
    # .. = ai_core
    # ../.. = mesh-mind
    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    @property
    def DB_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/db/mesh_mind.db")

    @property
    def CHROMA_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/vector_store")

    @property
    def MEDIA_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/media")

    @property
    def DOCS_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/docs")
    
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
        env_file=os.path.join(PROJECT_ROOT, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()
