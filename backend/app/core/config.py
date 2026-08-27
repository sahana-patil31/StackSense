import os
import secrets
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "stacksense-api"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/stacksense"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "stacksense"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    allowed_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    embedding_provider: str = "local"
    embedding_model: str = "local-hash-v1"
    llm_provider: str = "local"
    llm_model: str = "local-grounded-v1"
    llm_api_key: str | None = None
    auth_secret: str = secrets.token_urlsafe(32)
    auth_token_ttl_minutes: int = 60
    testing: bool = False
    code_analysis_allowed_root: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def cors_origins(self) -> List[str]:
        return self.allowed_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
