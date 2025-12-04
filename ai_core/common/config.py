import os
from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: Literal["dev", "prod"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"
    
    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    @property
    def DB_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/db/mesh_mind.db")

    @property
    def SESSION_DB_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/db/mesh_mind_sessions.db")

    @property
    def MEDIA_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/media")

    @property
    def DOCS_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/docs")

    @property
    def IMAGES_PATH(self) -> str:
        return os.path.join(self.PROJECT_ROOT, "data/images")
    
    # API Keys
    GOOGLE_API_KEY: str
    
    # Models
    GEMINI_MODEL_FAST: str = "gemini-2.5-flash"
    GEMINI_MODEL_SMART: str = GEMINI_MODEL_FAST

    
    # Company
    COMPANY_DOMAINS: List[str] = []
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(PROJECT_ROOT, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()
