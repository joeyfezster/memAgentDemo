from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.memory_tools import SearchPastConversationsTool
from app.crud import conversation as conversation_crud
from app.models.conversation import Conversation
from app.models.types import MessageRole
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import get_settings
from app.services.agent_service import AgentService
from tests.conftest import consume_streaming_response

pytestmark = [pytest.mark.asyncio, pytest.mark.expensive]
TEST_MODEL = "claude-sonnet-4-5-20250929"


@pytest_asyncio.fixture
async def memory_test_user(session: AsyncSession) -> User:
    user = User(
        email=f"memory-agent-test-{uuid.uuid4()}@example.com",
        display_name="Memory Agent Tester",
        hashed_password=get_password_hash("password123"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def seeded_past_conversations(
    session: AsyncSession, memory_test_user: User
) -> tuple[AgentService, User, list[Conversation]]:
    conversations = []
    now = datetime.now(UTC)

    conv1 = await conversation_crud.create_conversation(
        session, user_id=memory_test_user.id
    )
    conv1.title = "Dallas Cannibalization Study"
    conv1.created_at = now - timedelta(days=3)

    messages_conv1 = [
        (
            MessageRole.USER,
            "I need to analyze cannibalization risk for our proposed Dallas infill site near the existing Plano and Richardson locations.",
        ),
        (
            MessageRole.AGENT,
            "I'll analyze the trade area overlap between the proposed site and your existing stores to assess cannibalization impact.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "analyze_cannibalization",
                "tool_input": {
                    "proposed_location": "Dallas infill",
                    "existing_stores": ["plano", "richardson"],
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_trade_area_overlap",
                "tool_input": {
                    "store_1": "plano",
                    "store_2": "richardson",
                    "proposed_site": "dallas_infill",
                },
            },
        ),
        (
            MessageRole.AGENT,
            "Based on trade area analysis, the proposed Dallas infill would have a 22% overlap with your Plano store and 18% overlap with Richardson. The total cannibalization impact is estimated at 15% reduction in visits to existing stores, but the new location would capture an additional 40% new market share from competitors.",
        ),
    ]

    for role, content, *metadata in messages_conv1:
        tool_metadata = metadata[0] if metadata else None
        await conversation_crud.add_message_to_conversation(
            session,
            conv1.id,
            role=role.value,
            content=content,
            tool_metadata=tool_metadata,
        )

    await session.commit()
    await session.refresh(conv1)
    conversations.append(conv1)

    conv2 = await conversation_crud.create_conversation(
        session, user_id=memory_test_user.id
    )
    conv2.title = "Austin Site Evaluation"
    conv2.created_at = now - timedelta(days=5)

    messages_conv2 = [
        (
            MessageRole.USER,
            "Can you evaluate the Austin Westgate Shopping Center site for us?",
        ),
        (
            MessageRole.AGENT,
            "I'll analyze the Westgate Shopping Center location for you.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_location_details",
                "tool_input": {
                    "location": "Westgate Shopping Center Austin",
                    "include_demographics": True,
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_foot_traffic_trends",
                "tool_input": {
                    "location": "westgate_austin",
                    "time_period": "12_months",
                },
            },
        ),
        (
            MessageRole.AGENT,
            "The Austin Westgate site shows strong demographics with median household income of $78K and high daytime population from nearby offices. Foot traffic analysis shows 15K daily visits with peak traffic during lunch hours.",
        ),
    ]

    for role, content, *metadata in messages_conv2:
        tool_metadata = metadata[0] if metadata else None
        await conversation_crud.add_message_to_conversation(
            session,
            conv2.id,
            role=role.value,
            content=content,
            tool_metadata=tool_metadata,
        )

    await session.commit()
    await session.refresh(conv2)
    conversations.append(conv2)

    settings = get_settings()
    agent_service = AgentService(settings)
    agent_service.model = TEST_MODEL
    return agent_service, memory_test_user, conversations


async def test_agent_searches_memory_on_reference_to_past(
    session: AsyncSession,
    seeded_past_conversations: tuple[AgentService, User, list[Conversation]],
):
    """Validates agent calls search tool when user references past conversation and returns relevant content."""
    agent_service, user, past_conversations = seeded_past_conversations

    conversation = await conversation_crud.create_conversation(session, user_id=user.id)

    user_message = "What were those cannibalization percentages we discussed before for the Dallas site?"

    await conversation_crud.add_message_to_conversation(
        session, conversation.id, role=MessageRole.USER.value, content=user_message
    )

    response = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conversation.id,
            user_message_content=user_message,
            user=user,
            session=session,
        )
    )

    assert response.metadata is not None
    tool_interactions = response.metadata.tool_interactions
    assert len(tool_interactions) > 0

    search_calls = [
        t
        for t in tool_interactions
        if t.type == "tool_use" and t.name == SearchPastConversationsTool.name
    ]
    assert len(search_calls) >= 1

    assert "22%" in response.text or "18%" in response.text or "15%" in response.text


async def test_agent_does_not_search_for_general_questions(
    session: AsyncSession,
    seeded_past_conversations: tuple[AgentService, User, list[Conversation]],
):
    """Validates agent does not call search tool for general knowledge questions."""
    agent_service, user, _ = seeded_past_conversations

    conversation = await conversation_crud.create_conversation(session, user_id=user.id)

    user_message = "What is cannibalization in retail?"

    await conversation_crud.add_message_to_conversation(
        session, conversation.id, role=MessageRole.USER.value, content=user_message
    )

    response = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conversation.id,
            user_message_content=user_message,
            user=user,
            session=session,
        )
    )

    if response.metadata:
        tool_interactions = response.metadata.tool_interactions
        search_calls = [
            t
            for t in tool_interactions
            if t.type == "tool_use" and t.name == SearchPastConversationsTool.name
        ]
        assert len(search_calls) == 0

    assert len(response.text) > 50


async def test_agent_searches_with_synonyms(
    session: AsyncSession,
    seeded_past_conversations: tuple[AgentService, User, list[Conversation]],
):
    """Validates agent uses multiple keywords and synonyms when searching for past conversations."""
    agent_service, user, _ = seeded_past_conversations

    conversation = await conversation_crud.create_conversation(session, user_id=user.id)

    user_message = "Show me that overlap analysis we did for the Dallas location"

    await conversation_crud.add_message_to_conversation(
        session, conversation.id, role=MessageRole.USER.value, content=user_message
    )

    response = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conversation.id,
            user_message_content=user_message,
            user=user,
            session=session,
        )
    )

    assert response.metadata is not None
    tool_interactions = response.metadata.tool_interactions
    search_calls = [
        t
        for t in tool_interactions
        if t.type == "tool_use" and t.name == SearchPastConversationsTool.name
    ]
    assert len(search_calls) >= 1

    search_input = search_calls[0].input
    keywords = search_input.get("keywords", [])
    assert (
        len(keywords) >= 2
    ), "Agent should use multiple keywords/synonyms for better recall"


async def test_agent_retrieves_correct_conversation(
    session: AsyncSession,
    seeded_past_conversations: tuple[AgentService, User, list[Conversation]],
):
    """Validates agent retrieves and references the correct conversation when asked about specific past topic."""
    agent_service, user, past_conversations = seeded_past_conversations

    conversation = await conversation_crud.create_conversation(session, user_id=user.id)

    user_message = "What did we find out about the Austin Westgate location?"

    await conversation_crud.add_message_to_conversation(
        session, conversation.id, role=MessageRole.USER.value, content=user_message
    )

    response = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conversation.id,
            user_message_content=user_message,
            user=user,
            session=session,
        )
    )

    assert response.metadata is not None
    tool_interactions = response.metadata.tool_interactions
    search_calls = [
        t
        for t in tool_interactions
        if t.type == "tool_use" and t.name == SearchPastConversationsTool.name
    ]
    assert len(search_calls) >= 1

    response_text_lower = response.text.lower()
    assert "austin" in response_text_lower or "westgate" in response_text_lower
    assert any(
        term in response_text_lower
        for term in ["78k", "$78", "median household", "foot traffic", "15k"]
    )


async def test_agent_no_results_handling(
    session: AsyncSession,
    memory_test_user: User,
):
    """Validates agent gracefully handles queries about conversations that don't exist in history."""
    settings = get_settings()
    agent_service = AgentService(settings)
    agent_service.model = TEST_MODEL

    conversation = await conversation_crud.create_conversation(
        session, user_id=memory_test_user.id
    )

    user_message = "What did we discuss about the Seattle expansion last month?"

    await conversation_crud.add_message_to_conversation(
        session, conversation.id, role=MessageRole.USER.value, content=user_message
    )

    response = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conversation.id,
            user_message_content=user_message,
            user=memory_test_user,
            session=session,
        )
    )

    assert response.text is not None
    assert len(response.text) > 20

    response_text_lower = response.text.lower()
    assert any(
        phrase in response_text_lower
        for phrase in [
            "don't have",
            "no record",
            "haven't discussed",
            "don't recall",
            "no previous",
            "no past",
            "nothing on",
            "no information",
            "no details",
            "no conversations",
            "i don't",
            "i couldn't",
            "couldn't find",
        ]
    )
