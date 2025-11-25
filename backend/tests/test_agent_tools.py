from dataclasses import asdict

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.crud import conversation as conversation_crud
from app.models.types import MessageRole
from app.models.user import User
from app.services.agent_service import AgentService
from tests.conftest import consume_streaming_response

pytestmark = [pytest.mark.asyncio, pytest.mark.expensive]
TEST_MODEL = "claude-sonnet-4-5-20250929"


@pytest.fixture
def settings():
    return get_settings()


class BrokenTool:
    name = "broken_tool"
    description = (
        "A tool that always fails. Use this when the user asks to break things."
    )

    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {"dummy": {"type": "string"}},
        }

    async def execute(self, **kwargs):
        raise Exception("Simulated tool error")


class StrictTool:
    name = "strict_tool"
    description = "A tool that requires a specific secret code."

    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        }

    async def execute(self, code: str, **kwargs):
        if code != "secret_code":
            raise ValueError("Wrong code. The code is 'secret_code'")
        return {"status": "access_granted"}


class TestAgentToolCalling:
    """Test ReAct loop with real tool execution (Integration Tests)"""

    async def test_single_tool_call_search_places(
        self,
        session: AsyncSession,
        test_user_sarah: User,
        settings,
    ):
        """User asks to find places, agent calls search_places once"""
        conv = await conversation_crud.create_conversation(
            session, user_id=test_user_sarah.id
        )
        user_query = "Find the top 5 Starbucks locations in San Francisco"
        agent_service = AgentService(settings)
        agent_service.model = TEST_MODEL

        response = await consume_streaming_response(
            agent_service.stream_response_with_tools(
                conversation_id=conv.id,
                user_message_content=user_query,
                user=test_user_sarah,
                session=session,
            )
        )

        assert response.text, "Should get a response"
        assert response.metadata.stop_reason in ["end_turn", "max_iterations"]
        assert response.metadata.iteration_count >= 1

        response_lower = response.text.lower()
        assert any(
            word in response_lower
            for word in [
                "starbucks",
                "coffee",
                "shop",
                "location",
                "san francisco",
                "5",
            ]
        ), "Response should mention search results"

        tool_interactions = response.metadata.tool_interactions
        assert len(tool_interactions) > 0, "Should have tool interactions"

        tool_uses = [t for t in tool_interactions if t.type == "tool_use"]
        assert any(
            t.name == "search_places" for t in tool_uses
        ), "Should call search_places tool"

        tool_results = [t for t in tool_interactions if t.type == "tool_result"]
        assert len(tool_results) > 0, "Should have tool results"
        assert not any(t.is_error for t in tool_results), "Should not have errors"

    async def test_multi_tool_sequence(
        self,
        session: AsyncSession,
        test_user_sarah: User,
        settings,
    ):
        """Agent makes multiple tool calls in sequence"""
        conv = await conversation_crud.create_conversation(
            session, user_id=test_user_sarah.id
        )
        user_query = "First find Starbucks locations in San Francisco. After you get the results, you MUST use the get_place_summary tool for the first location in the list."

        agent_service = AgentService(settings)
        agent_service.model = TEST_MODEL

        response = await consume_streaming_response(
            agent_service.stream_response_with_tools(
                conversation_id=conv.id,
                user_message_content=user_query,
                user=test_user_sarah,
                session=session,
            )
        )

        assert response.text

        assert response.text
        assert response.metadata.iteration_count >= 1
        assert response.text
        assert response.metadata.stop_reason in ["end_turn", "max_iterations"]

        tool_uses = [
            t for t in response.metadata.tool_interactions if t.type == "tool_use"
        ]
        tool_names = {t.name for t in tool_uses}

        assert "search_places" in tool_names, "Should call search_places"
        assert (
            len(tool_uses) >= 2
        ), "Should have at least 2 tool calls for this multi-step task"

    async def test_tool_error_handling(
        self,
        session: AsyncSession,
        test_user_sarah: User,
        settings,
    ):
        """Agent handles tool execution errors gracefully"""
        conv = await conversation_crud.create_conversation(
            session, user_id=test_user_sarah.id
        )
        user_query = "Please use the broken_tool to simulate an error."

        agent_service = AgentService(settings)
        agent_service.model = TEST_MODEL
        agent_service.tool_registry.register(BrokenTool())

        response = await consume_streaming_response(
            agent_service.stream_response_with_tools(
                conversation_id=conv.id,
                user_message_content=user_query,
                user=test_user_sarah,
                session=session,
            )
        )

        assert response.text, "Should get a response even if tool fails"

        tool_interactions = response.metadata.tool_interactions
        tool_results = [t for t in tool_interactions if t.type == "tool_result"]

        assert any(
            t.is_error for t in tool_results
        ), "Should have recorded an error in tool results"

    async def test_tool_input_validation(
        self,
        session: AsyncSession,
        test_user_sarah: User,
        settings,
    ):
        """Agent corrects invalid tool input based on error feedback"""
        conv = await conversation_crud.create_conversation(
            session, user_id=test_user_sarah.id
        )
        user_query = "Use the strict_tool. Try the code 'guess' first. If that fails, the error message will tell you the real code."

        agent_service = AgentService(settings)
        agent_service.model = TEST_MODEL
        agent_service.tool_registry.register(StrictTool())

        response = await consume_streaming_response(
            agent_service.stream_response_with_tools(
                conversation_id=conv.id,
                user_message_content=user_query,
                user=test_user_sarah,
                session=session,
            )
        )

        assert response.text

        tool_interactions = response.metadata.tool_interactions
        tool_uses = [t for t in tool_interactions if t.type == "tool_use"]

        assert len(tool_uses) >= 2, "Should have retried after validation error"

        assert tool_uses[0].input["code"] == "guess"

        assert tool_uses[-1].input["code"] == "secret_code"

    async def test_max_iterations_safety(
        self,
        session: AsyncSession,
        test_user_sarah: User,
        settings,
    ):
        """Agent stops after max iterations, preventing runaway tool use loops"""
        conv = await conversation_crud.create_conversation(
            session, user_id=test_user_sarah.id
        )
        user_query = "Find coffee shops in San Francisco. Then find coffee shops in New York. Then find coffee shops in Chicago. Then search previous conversations for 'coffee' and tell me which of these locations we have already talked about."

        agent_service = AgentService(settings)
        agent_service.model = TEST_MODEL
        agent_service.max_iterations_streaming = 1  # Limit to 1 tool-use cycle

        response = await consume_streaming_response(
            agent_service.stream_response_with_tools(
                conversation_id=conv.id,
                user_message_content=user_query,
                user=test_user_sarah,
                session=session,
            )
        )

        assert response.metadata.iteration_count == 1, "Should stop after 1 iteration"
        assert (
            response.metadata.stop_reason == "max_iterations"
        ), f"Expected max_iterations stop, got {response.metadata.stop_reason}"

    async def test_conversation_persistence_with_tools(
        self,
        session: AsyncSession,
        test_user_sarah: User,
        settings,
    ):
        """Tool interactions are properly stored in message.metadata in database"""
        conv = await conversation_crud.create_conversation(
            session, user_id=test_user_sarah.id
        )
        user_query = "Find shopping malls in Los Angeles"

        messages_before = await conversation_crud.get_conversation_messages(
            session, conv.id
        )
        assert len(messages_before) == 0

        agent_service = AgentService(settings)
        agent_service.model = TEST_MODEL
        response = await consume_streaming_response(
            agent_service.stream_response_with_tools(
                conversation_id=conv.id,
                user_message_content=user_query,
                user=test_user_sarah,
                session=session,
            )
        )

        await conversation_crud.add_message_to_conversation(
            session,
            conversation_id=conv.id,
            role=MessageRole.AGENT.value,
            content=response.text,
            tool_metadata=asdict(response.metadata) if response.metadata else None,
        )

        messages_after = await conversation_crud.get_conversation_messages(
            session, conv.id
        )
        agent_messages = [
            m for m in messages_after if m.role == MessageRole.AGENT.value
        ]
        assert len(agent_messages) == 1

        persisted_msg = agent_messages[0]
        assert persisted_msg.tool_metadata is not None
        assert "tool_interactions" in persisted_msg.tool_metadata

    async def test_no_tool_needed(
        self,
        session: AsyncSession,
        test_user_sarah: User,
        settings,
    ):
        """Agent responds without tools for simple conversational queries"""
        conv = await conversation_crud.create_conversation(
            session, user_id=test_user_sarah.id
        )
        user_query = "Hello, how are you today?"

        agent_service = AgentService(settings)
        agent_service.model = TEST_MODEL
        response = await consume_streaming_response(
            agent_service.stream_response_with_tools(
                conversation_id=conv.id,
                user_message_content=user_query,
                user=test_user_sarah,
                session=session,
            )
        )

        assert response.text
        assert len(response.text) > 0

        if response.metadata:
            assert len(response.metadata.tool_interactions) == 0
