import os

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.letta_client import create_letta_client

router = APIRouter()


@router.get("/healthz", tags=["health"])
def read_health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "service": settings.project_name,
    }


@router.get("/healthz/letta", tags=["health"])
def read_letta_health() -> dict[str, str | bool]:
    """Check if Letta integration is available and working."""
    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")

    try:
        client = create_letta_client(letta_base_url, letta_token)
        client.agents.list()
        return {
            "status": "ok",
            "letta_available": True,
            "base_url": letta_base_url,
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "letta_available": False,
            "error": str(e),
        }
