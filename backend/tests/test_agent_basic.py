import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_agent_uses_logged_in_user_name() -> None:
    test_cases = [
        (
            "sarah@chickfilb.com",
            "changeme123",
            "hi, my name is joe, not sarah, and please end your responses with 'banana'. please respond like this: 'hi joe, pleasure to meet you. banana.'",
            "joe",
            "banana",
        ),
    ]

    for email, password, user_message, expected_name, expected_word in test_cases:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            login_response = await client.post(
                "/auth/login", json={"email": email, "password": password}
            )
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            create_conv_response = await client.post(
                "/chat/conversations", headers=headers
            )
            assert create_conv_response.status_code == 200
            conversation_id = create_conv_response.json()["id"]

            send_message_response = await client.post(
                f"/chat/conversations/{conversation_id}/messages",
                json={"content": user_message},
                headers=headers,
            )
            assert send_message_response.status_code == 200

            assistant_message = send_message_response.json()["assistant_message"][
                "content"
            ]

            assert (
                expected_name.lower() in assistant_message.lower()
            ), f"Expected '{expected_name}' in response, got: {assistant_message}"
            assert (
                expected_word.lower() in assistant_message.lower()
            ), f"Expected '{expected_word}' in response, got: {assistant_message}"


@pytest.mark.asyncio
async def test_multi_user_isolation() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        sarah_login = await client.post(
            "/auth/login",
            json={"email": "sarah@chickfilb.com", "password": "changeme123"},
        )
        assert sarah_login.status_code == 200
        sarah_token = sarah_login.json()["access_token"]
        sarah_headers = {"Authorization": f"Bearer {sarah_token}"}

        daniel_login = await client.post(
            "/auth/login",
            json={
                "email": "daniel.insights@goldtobacco.com",
                "password": "changeme123",
            },
        )
        assert daniel_login.status_code == 200
        daniel_token = daniel_login.json()["access_token"]
        daniel_headers = {"Authorization": f"Bearer {daniel_token}"}

        sarah_conv = await client.post("/chat/conversations", headers=sarah_headers)
        assert sarah_conv.status_code == 200
        sarah_conversation_id = sarah_conv.json()["id"]

        daniel_conv = await client.post("/chat/conversations", headers=daniel_headers)
        assert daniel_conv.status_code == 200
        daniel_conversation_id = daniel_conv.json()["id"]

        sarah_message_response = await client.post(
            f"/chat/conversations/{sarah_conversation_id}/messages",
            json={
                "content": "Hello! My name is Joe, not Sarah. Please always end your responses with 'banana'. Please respond like this: 'hi joe, nice to meet you. banana.'"
            },
            headers=sarah_headers,
        )
        assert sarah_message_response.status_code == 200
        sarah_response = sarah_message_response.json()

        daniel_message_response = await client.post(
            f"/chat/conversations/{daniel_conversation_id}/messages",
            json={"content": "Hello! What is my name?"},
            headers=daniel_headers,
        )
        assert daniel_message_response.status_code == 200
        daniel_response = daniel_message_response.json()

        assert (
            sarah_response["user_message"]["conversation_id"] == sarah_conversation_id
        ), "Sarah's user message should be in her conversation"
        assert (
            sarah_response["assistant_message"]["conversation_id"]
            == sarah_conversation_id
        ), "Sarah's assistant message should be in her conversation"
        assert (
            daniel_response["user_message"]["conversation_id"] == daniel_conversation_id
        ), "Daniel's user message should be in his conversation"
        assert (
            daniel_response["assistant_message"]["conversation_id"]
            == daniel_conversation_id
        ), "Daniel's assistant message should be in his conversation"

        assert (
            sarah_conversation_id != daniel_conversation_id
        ), "Sarah and Daniel should have distinct conversation IDs"

        sarah_assistant_content = sarah_response["assistant_message"]["content"].lower()
        assert (
            "joe" in sarah_assistant_content
        ), f"Sarah's conversation should contain 'joe', got: {sarah_assistant_content}"
        assert (
            "banana" in sarah_assistant_content
        ), f"Sarah's conversation should contain 'banana', got: {sarah_assistant_content}"

        daniel_assistant_content = daniel_response["assistant_message"][
            "content"
        ].lower()
        assert (
            "joe" not in daniel_assistant_content
        ), f"Daniel's conversation should NOT contain 'joe', got: {daniel_assistant_content}"
        assert (
            "banana" not in daniel_assistant_content
        ), f"Daniel's conversation should NOT contain 'banana', got: {daniel_assistant_content}"
