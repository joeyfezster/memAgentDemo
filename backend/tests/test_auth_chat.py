from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app

TEST_EMAIL = "daniel.insights@goldtobacco.com"
TEST_PASSWORD = "changeme123"


@pytest.mark.asyncio
async def test_login_me_and_chat_flow():
    async with AsyncClient(app=app, base_url="http://test") as client:
        login_response = await client.post(
            "/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200
        payload = login_response.json()
        assert payload["access_token"]
        assert payload["token_type"] == "bearer"
        user = payload["user"]
        assert user["email"] == TEST_EMAIL
        token = payload["access_token"]

        me_response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        me_payload = me_response.json()
        assert me_payload["email"] == TEST_EMAIL

        chat_response = await client.post(
            "/chat/messages",
            json={"message": "Hello"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert chat_response.status_code == 200
        chat_payload = chat_response.json()
        assert chat_payload["reply"].lower().startswith("hi ")
        assert user["display_name"].lower() in chat_payload["reply"].lower()
