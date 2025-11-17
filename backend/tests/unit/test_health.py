import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "environment" in payload
    assert "service" in payload


@pytest.mark.asyncio
async def test_letta_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz/letta")
    assert response.status_code == 200
    payload = response.json()
    assert "letta_available" in payload
    assert isinstance(payload["letta_available"], bool)
