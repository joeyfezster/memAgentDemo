from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.memory_tools import SearchPastConversationsTool
from app.core.security import get_password_hash
from app.models.conversation import Conversation
from app.models.types import MessageRole
from app.models.user import User


@pytest_asyncio.fixture
async def tool_user(session: AsyncSession) -> User:
    user = User(
        email=f"tooltester-{uuid.uuid4()}@example.com",
        display_name="Tool Tester",
        hashed_password=get_password_hash("password123"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_memory_tool_with_valid_session(
    session: AsyncSession,
    tool_user: User,
):
    conv = Conversation(
        user_id=tool_user.id,
        title="Cannibalization Study",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=2),
    )
    session.add(conv)
    await session.flush()

    conv.add_message(
        MessageRole.USER.value,
        "I need to analyze cannibalization risk for the Dallas site.",
    )
    conv.add_message(
        MessageRole.AGENT.value,
        "I'll analyze the cannibalization overlap for your Dallas location.",
    )

    await session.commit()
    await session.refresh(conv)

    tool = SearchPastConversationsTool()
    result = await tool.execute(
        keywords=["cannibalization"],
        session=session,
        user_id=tool_user.id,
    )

    assert isinstance(result, dict)
    assert "conversations" in result
    assert "total_found" in result
    assert result["total_found"] >= 1
    assert len(result["conversations"]) >= 1

    conv_result = result["conversations"][0]
    assert "matched_snippet" in conv_result
    assert "**[MATCH " in conv_result["matched_snippet"]
    assert "cannibalization" in conv_result["matched_snippet"].lower()


@pytest.mark.asyncio
async def test_memory_tool_without_session(tool_user: User):
    tool = SearchPastConversationsTool()
    result = await tool.execute(
        keywords=["test"],
        user_id=tool_user.id,
    )

    assert isinstance(result, dict)
    assert "error" in result
    assert "Database session not available" in result["error"]
    assert result["conversations"] == []
    assert result["total_found"] == 0


@pytest.mark.asyncio
async def test_memory_tool_without_user_id(session: AsyncSession):
    tool = SearchPastConversationsTool()
    result = await tool.execute(
        keywords=["test"],
        session=session,
    )

    assert isinstance(result, dict)
    assert "error" in result
    assert "Database session not available" in result["error"]
    assert result["conversations"] == []
    assert result["total_found"] == 0


@pytest.mark.asyncio
async def test_memory_tool_user_isolation(
    session: AsyncSession,
    tool_user: User,
):
    user2 = User(
        email=f"user2-{uuid.uuid4()}@example.com",
        display_name="User 2",
        hashed_password=get_password_hash("password456"),
    )
    session.add(user2)
    await session.flush()

    conv1 = Conversation(
        user_id=tool_user.id,
        title="User 1 Dallas Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    session.add(conv1)
    await session.flush()
    conv1.add_message(MessageRole.USER.value, "User 1 analyzing Dallas site")

    conv2 = Conversation(
        user_id=user2.id,
        title="User 2 Dallas Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    session.add(conv2)
    await session.flush()
    conv2.add_message(MessageRole.USER.value, "User 2 different Dallas analysis")

    await session.commit()
    await session.refresh(conv1)
    await session.refresh(conv2)
    await session.refresh(user2)

    tool = SearchPastConversationsTool()
    result_user1 = await tool.execute(
        keywords=["Dallas"],
        session=session,
        user_id=tool_user.id,
    )

    assert isinstance(result_user1, dict)
    assert result_user1["total_found"] >= 1
    snippet_text = result_user1["conversations"][0]["matched_snippet"]
    assert "User 1" in snippet_text
    assert "User 2" not in snippet_text


@pytest.mark.asyncio
async def test_memory_tool_empty_keywords(
    session: AsyncSession,
    tool_user: User,
):
    tool = SearchPastConversationsTool()
    result = await tool.execute(
        keywords=[],
        session=session,
        user_id=tool_user.id,
    )

    # Empty keywords should trigger validation error
    assert isinstance(result, dict)
    assert "error" in result or result["total_found"] == 0


@pytest.mark.asyncio
async def test_memory_tool_no_matches(
    session: AsyncSession,
    tool_user: User,
):
    conv = Conversation(
        user_id=tool_user.id,
        title="Test Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    session.add(conv)
    await session.flush()
    conv.add_message(MessageRole.USER.value, "Regular content here")

    await session.commit()
    await session.refresh(conv)

    tool = SearchPastConversationsTool()
    result = await tool.execute(
        keywords=["nonexistent_xyz123"],
        session=session,
        user_id=tool_user.id,
    )

    assert isinstance(result, dict)
    assert result["total_found"] == 0
    assert result["conversations"] == []


@pytest.mark.asyncio
async def test_memory_tool_match_markers(
    session: AsyncSession,
    tool_user: User,
):
    conv = Conversation(
        user_id=tool_user.id,
        title="Site Analysis",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    session.add(conv)
    await session.flush()

    conv.add_message(MessageRole.USER.value, "First message")
    conv.add_message(
        MessageRole.USER.value, "Target message with keyword cannibalization here"
    )
    conv.add_message(MessageRole.USER.value, "Third message")

    await session.commit()
    await session.refresh(conv)

    tool = SearchPastConversationsTool()
    result = await tool.execute(
        keywords=["cannibalization"],
        session=session,
        user_id=tool_user.id,
    )

    assert isinstance(result, dict)
    assert result["total_found"] >= 1
    snippet = result["conversations"][0]["matched_snippet"]
    assert "**[MATCH " in snippet
    assert snippet.count("**[MATCH ") >= 1
