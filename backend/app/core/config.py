from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    project_name: str = "memAgent Demo API"
    environment: str = "local"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
    jwt_secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    persona_seed_password: str = "changeme123"
    anthropic_api_key: str
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536


@lru_cache
def get_settings() -> Settings:
    return Settings()
