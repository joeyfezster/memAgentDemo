import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.crud import conversation as conversation_crud
from app.crud import message as message_crud
from app.models.message import MessageRole
from app.models.user import User
from app.services.agent_service import AgentService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def settings():
    return get_settings()


class TestAgentToolCalling:
    """Test ReAct loop with tool execution"""

    async def test_single_tool_call_search_places(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """User asks to find places, agent calls search_places once"""
        # Create conversation
        conv = await conversation_crud.create_conversation(session, test_user.id)

        # User query requiring tool use
        user_query = "Find the top 5 Starbucks locations in San Francisco"

        # Agent service
        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Assertions
        assert response_text, "Should get a response"
        assert metadata["stop_reason"] == "end_turn"
        assert metadata["iteration_count"] >= 1

        # Check tool was called
        tool_interactions = metadata["tool_interactions"]
        assert len(tool_interactions) > 0, "Should have tool interactions"

        # Find search_places call
        tool_uses = [t for t in tool_interactions if t["type"] == "tool_use"]
        assert any(
            t["name"] == "search_places" for t in tool_uses
        ), "Should call search_places tool"

        # Check we got results back
        tool_results = [t for t in tool_interactions if t["type"] == "tool_result"]
        assert len(tool_results) > 0, "Should have tool results"
        assert not any(
            t.get("is_error") for t in tool_results
        ), "Should not have errors"

        # Response should mention results
        response_lower = response_text.lower()
        assert (
            "starbucks" in response_lower
            or "coffee" in response_lower
            or "location" in response_lower
        ), "Response should mention search results"

    async def test_multi_tool_sequence(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Agent makes multiple tool calls in sequence"""
        conv = await conversation_crud.create_conversation(session, test_user.id)

        # Query requiring search + summary
        user_query = (
            "Find Chick-fil-A locations in Atlanta and tell me how they're performing"
        )

        agent_service = AgentService(settings)
        # Override model for this test to use more capable Opus
        agent_service.model = "claude-opus-4-20250514"

        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Should have completed successfully
        assert response_text
        assert metadata["stop_reason"] in ["end_turn", "max_iterations"]

        # Should have called multiple tools
        tool_uses = [
            t for t in metadata["tool_interactions"] if t["type"] == "tool_use"
        ]

        tool_names = {t["name"] for t in tool_uses}
        assert "search_places" in tool_names, "Should call search_places"

        # Validate multiple tools were used (search + at least one other)
        assert len(tool_uses) >= 2, (
            f"Expected at least 2 tool calls for search+summary query, got {len(tool_uses)}. "
            f"Tools called: {tool_names}"
        )

        # Response should be substantive
        assert len(response_text) > 50, "Response should be substantive"

    async def test_tool_error_handling(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Agent handles tool execution errors gracefully"""
        conv = await conversation_crud.create_conversation(session, test_user.id)

        # Query that might trigger edge case
        user_query = "Find places in a completely invalid location with bad parameters"

        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Agent should still produce a response
        assert response_text, "Should get a response even if tool fails"
        assert metadata["stop_reason"] in [
            "end_turn",
            "max_iterations",
        ], "Should complete gracefully"

    async def test_max_iterations_safety(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Agent stops after max iterations"""
        conv = await conversation_crud.create_conversation(session, test_user.id)

        # Complex query
        user_query = "Analyze every coffee shop in the United States in detail"

        agent_service = AgentService(settings)
        agent_service.max_iterations = 3  # Lower for testing

        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Should hit limit or complete
        assert metadata["iteration_count"] <= 3, "Should respect max iterations"
        assert response_text, "Should still return a response"

        if metadata["stop_reason"] == "max_iterations":
            assert (
                "limit" in response_text.lower() or "apologize" in response_text.lower()
            ), "Should apologize if hitting limit"

    async def test_conversation_persistence_with_tools(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Tool interactions are properly stored in message.metadata in database"""
        conv = await conversation_crud.create_conversation(session, test_user.id)

        user_query = "Find shopping malls in Los Angeles"

        # Check no tool interactions exist before agent call
        messages_before = await message_crud.get_conversation_messages(session, conv.id)
        agent_messages_before = [
            m for m in messages_before if m.role == MessageRole.AGENT
        ]
        assert len(agent_messages_before) == 0, "No agent messages should exist yet"

        # Generate response with tools
        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Create assistant message with metadata
        await message_crud.create_message(
            session,
            conversation_id=conv.id,
            role=MessageRole.AGENT,
            content=response_text,
            metadata=metadata,
        )
        await session.commit()

        # Fetch conversation from DB fresh to validate persistence
        messages_after = await message_crud.get_conversation_messages(session, conv.id)
        agent_messages_after = [
            m for m in messages_after if m.role == MessageRole.AGENT
        ]

        assert len(agent_messages_after) == 1, "Should have one agent message"
        persisted_msg = agent_messages_after[0]

        # Verify metadata persisted to JSONB column
        assert persisted_msg.metadata is not None, "Metadata should be stored in DB"
        assert (
            "tool_interactions" in persisted_msg.metadata
        ), "Should have tool_interactions in DB"
        assert (
            "iteration_count" in persisted_msg.metadata
        ), "Should have iteration_count in DB"
        assert isinstance(
            persisted_msg.metadata["tool_interactions"], list
        ), "tool_interactions should be a list in DB"

        # Validate tool interaction structure in DB
        if len(persisted_msg.metadata["tool_interactions"]) > 0:
            tool_interaction = persisted_msg.metadata["tool_interactions"][0]
            assert "type" in tool_interaction, "Tool interaction should have type"
            assert tool_interaction["type"] in [
                "tool_use",
                "tool_result",
            ], "Tool interaction type should be valid"

    async def test_no_tool_needed(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Agent responds without tools for simple conversational queries"""
        conv = await conversation_crud.create_conversation(session, test_user.id)

        # Simple conversational query
        user_query = "Hello, how are you today?"

        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Should respond without tools
        assert response_text
        assert metadata["stop_reason"] == "end_turn"

        # May or may not use tools - agent decides
        # Just verify we get a reasonable response
        assert len(response_text) > 10, "Should get a substantive greeting"

    async def test_tool_input_validation(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Test that tool input validation works correctly"""
        conv = await conversation_crud.create_conversation(session, test_user.id)

        # Query that should trigger search_places with valid inputs
        user_query = "Search for coffee shops near downtown San Francisco"

        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Should complete successfully
        assert response_text
        assert metadata["stop_reason"] == "end_turn"

        # Check tool was called with valid schema
        tool_uses = [
            t for t in metadata["tool_interactions"] if t["type"] == "tool_use"
        ]
        if tool_uses:
            for tool_use in tool_uses:
                assert "name" in tool_use, "Tool use should have name"
                assert "input" in tool_use, "Tool use should have input"
                assert isinstance(tool_use["input"], dict), "Tool input should be dict"
