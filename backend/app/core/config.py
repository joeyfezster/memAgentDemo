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

    # Letta Configuration
    # API key for Letta service - REQUIRED for agent functionality
    # Get your API key from https://app.letta.com/settings
    letta_api_key: str = ""

    # Optional: Custom Letta base URL (defaults to Letta's hosted service)
    # Set this if you're running a self-hosted Letta server
    letta_base_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
