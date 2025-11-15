from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/healthz", tags=["health"])
def read_health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "service": settings.project_name,
    }
