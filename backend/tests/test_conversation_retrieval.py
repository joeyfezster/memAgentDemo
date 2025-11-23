from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.db.base import Base
from app.models.conversation import Conversation
from app.models.message import MessageRole
from app.models.user import User
from app.services.conversation_retrieval import (
    filter_messages_by_date_range,
    filter_messages_by_role,
    search_conversations_fulltext,
)


@pytest_asyncio.fixture
async def test_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = AsyncSession(engine, expire_on_commit=False)
    try:
        yield async_session
    finally:
        await async_session.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        display_name="Test User",
        hashed_password=get_password_hash("password123"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def conversations_with_messages(
    test_session: AsyncSession, test_user: User
) -> list[Conversation]:
    now = datetime.now(UTC)

    conv1 = Conversation(
        user_id=test_user.id,
        title="Python asyncio discussion",
        messages_document=[
            {
                "id": "msg-1-1",
                "role": MessageRole.USER.value,
                "content": "How does asyncio work in Python?",
                "created_at": (now - timedelta(days=5)).isoformat(),
            },
            {
                "id": "msg-1-2",
                "role": MessageRole.AGENT.value,
                "content": "Asyncio is a library for concurrent programming using async/await.",
                "created_at": (now - timedelta(days=5, seconds=-30)).isoformat(),
            },
        ],
    )

    conv2 = Conversation(
        user_id=test_user.id,
        title="Database optimization",
        messages_document=[
            {
                "id": "msg-2-1",
                "role": MessageRole.USER.value,
                "content": "My database queries are slow",
                "created_at": (now - timedelta(days=2)).isoformat(),
            },
            {
                "id": "msg-2-2",
                "role": MessageRole.AGENT.value,
                "content": "Let's check your indexes and query plans",
                "created_at": (now - timedelta(days=2, seconds=-20)).isoformat(),
            },
        ],
    )

    conv3 = Conversation(
        user_id=test_user.id,
        title="React hooks tutorial",
        messages_document=[
            {
                "id": "msg-3-1",
                "role": MessageRole.USER.value,
                "content": "Can you explain React hooks?",
                "created_at": now.isoformat(),
            },
        ],
    )

    test_session.add_all([conv1, conv2, conv3])
    await test_session.commit()
    return [conv1, conv2, conv3]


@pytest.mark.asyncio
async def test_fulltext_search_finds_conversations(
    test_session: AsyncSession,
    test_user: User,
    conversations_with_messages: list[Conversation],
):
    results = await search_conversations_fulltext(
        test_session, test_user.id, "Python", limit=10
    )

    assert len(results) >= 1
    assert any("Python" in str(conv.messages_document) for conv in results)


@pytest.mark.asyncio
async def test_fulltext_search_respects_user_isolation(
    test_session: AsyncSession,
    test_user: User,
    conversations_with_messages: list[Conversation],
):
    user2 = User(
        email="user2@example.com",
        display_name="User 2",
        hashed_password=get_password_hash("password456"),
    )
    test_session.add(user2)
    await test_session.commit()
    await test_session.refresh(user2)

    conv_user2 = Conversation(
        user_id=user2.id,
        title="User 2 Python conversation",
        messages_document=[
            {
                "id": "msg-u2-1",
                "role": MessageRole.USER.value,
                "content": "Python question from user 2",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ],
    )
    test_session.add(conv_user2)
    await test_session.commit()

    results_user1 = await search_conversations_fulltext(
        test_session, test_user.id, "Python", limit=10
    )
    results_user2 = await search_conversations_fulltext(
        test_session, user2.id, "Python", limit=10
    )

    assert all(conv.user_id == test_user.id for conv in results_user1)
    assert all(conv.user_id == user2.id for conv in results_user2)


@pytest.mark.asyncio
async def test_filter_messages_by_role(conversations_with_messages: list[Conversation]):
    conv = conversations_with_messages[0]
    user_messages = filter_messages_by_role(conv, MessageRole.USER.value)
    agent_messages = filter_messages_by_role(conv, MessageRole.AGENT.value)

    assert len(user_messages) == 1
    assert len(agent_messages) == 1
    assert user_messages[0]["role"] == MessageRole.USER.value
    assert agent_messages[0]["role"] == MessageRole.AGENT.value


@pytest.mark.asyncio
async def test_filter_messages_by_date_range(
    conversations_with_messages: list[Conversation],
):
    conv = conversations_with_messages[0]
    now = datetime.now(UTC)
    start = now - timedelta(days=10)
    end = now

    filtered = filter_messages_by_date_range(conv, start, end)

    assert len(filtered) >= 1
    for msg in filtered:
        msg_date = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
        assert start <= msg_date <= end


@pytest.mark.asyncio
async def test_fulltext_search_no_results(
    test_session: AsyncSession,
    test_user: User,
    conversations_with_messages: list[Conversation],
):
    results = await search_conversations_fulltext(
        test_session, test_user.id, "nonexistent_keyword_xyz123", limit=10
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_fulltext_search_limit(test_session: AsyncSession, test_user: User):
    for i in range(15):
        conv = Conversation(
            user_id=test_user.id,
            title=f"Python tutorial {i}",
            messages_document=[
                {
                    "id": f"msg-{i}",
                    "role": MessageRole.USER.value,
                    "content": f"Python question {i}",
                    "created_at": datetime.now(UTC).isoformat(),
                }
            ],
        )
        test_session.add(conv)
    await test_session.commit()

    results = await search_conversations_fulltext(
        test_session, test_user.id, "Python", limit=5
    )

    assert len(results) == 5
