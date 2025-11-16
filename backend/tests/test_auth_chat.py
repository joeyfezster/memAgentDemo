from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.letta_client import LettaAgentResponse
from app.main import app
from app.services import pi_agent

TEST_EMAIL = "daniel.insights@goldtobacco.com"
TEST_PASSWORD = "test-password"


@pytest.mark.asyncio
async def test_login_me_and_chat_flow(monkeypatch):
    async def fake_provision(user, personas):
        return "agent-123"

    async def fake_send_message(agent_id, message):
        return LettaAgentResponse(
            agent_id=agent_id,
            message_content=f"Hello {message}",
            tool_calls=[],
        )

    monkeypatch.setattr(pi_agent.pi_agent_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        pi_agent.pi_agent_service,
        "provision_user_agent",
        fake_provision,
    )
    monkeypatch.setattr(
        pi_agent.pi_agent_service,
        "send_message",
        fake_send_message,
    )

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

        conversation_response = await client.post(
            "/chat/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert conversation_response.status_code == 200
        conversation_id = conversation_response.json()["id"]

        chat_response = await client.post(
            f"/chat/conversations/{conversation_id}/messages",
            json={"content": "Hello"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert chat_response.status_code == 200
        chat_payload = chat_response.json()
        assert chat_payload["assistant_message"]["content"].startswith("Hello")
        assert chat_payload["tool_calls"] == []
