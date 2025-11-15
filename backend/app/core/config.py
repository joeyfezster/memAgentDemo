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


@lru_cache
def get_settings() -> Settings:
    return Settings()
