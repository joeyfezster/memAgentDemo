from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.db.base import Base
from app.models.conversation import Conversation
from app.models.types import MessageRole
from app.models.user import User
from app.services.conversation_retrieval import (
    search_conversations_fulltext,
    search_messages_fulltext,
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
    """Verify fulltext search locates conversations containing search term."""
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
    """Ensure users only see their own conversations in search results."""
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
async def test_fulltext_search_no_results(
    test_session: AsyncSession,
    test_user: User,
    conversations_with_messages: list[Conversation],
):
    """Verify search returns empty list when no conversations match."""
    results = await search_conversations_fulltext(
        test_session, test_user.id, "nonexistent_keyword_xyz123", limit=10
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_fulltext_search_limit(test_session: AsyncSession, test_user: User):
    """Verify limit parameter correctly restricts number of results."""
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


@pytest.mark.asyncio
async def test_search_messages_fulltext_finds_keyword(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify message-level search finds messages containing keywords."""
    from datetime import UTC, datetime, timedelta

    conv = Conversation(
        user_id=test_user.id,
        title="Cannibalization Analysis",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=3),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(
        MessageRole.USER.value,
        "I need to analyze cannibalization risk for the Dallas infill site.",
    )
    conv.add_message(
        MessageRole.AGENT.value,
        "I'll analyze cannibalization overlap between your existing stores and the proposed Dallas infill location.",
    )

    await test_session.commit()
    await test_session.refresh(conv)

    results = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["cannibalization"],
        limit=10,
    )

    assert len(results) >= 1
    assert any(
        "cannibalization" in result.matched_message.content.lower()
        for result in results
    )


@pytest.mark.asyncio
async def test_search_messages_returns_context(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify matched messages include configured before/after context."""
    from datetime import UTC, datetime, timedelta

    conv = Conversation(
        user_id=test_user.id,
        title="Test Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(MessageRole.USER.value, "First message before target")
    conv.add_message(MessageRole.AGENT.value, "Second message before target")
    conv.add_message(
        MessageRole.USER.value, "Target message with cannibalization keyword"
    )
    conv.add_message(MessageRole.AGENT.value, "First message after target")
    conv.add_message(MessageRole.USER.value, "Second message after target")

    await test_session.commit()
    await test_session.refresh(conv)

    results = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["cannibalization"],
        limit=10,
        context_before=2,
        context_after=2,
    )

    assert len(results) >= 1
    result = results[0]

    assert isinstance(result.messages_before, list)
    assert isinstance(result.messages_after, list)
    assert len(result.messages_before) <= 2
    assert len(result.messages_after) <= 2


@pytest.mark.asyncio
async def test_search_messages_user_isolation(
    test_session: AsyncSession,
    test_user: User,
):
    """Ensure message search respects user boundaries."""
    from datetime import UTC, datetime, timedelta

    user2 = User(
        email="user2@example.com",
        display_name="User 2",
        hashed_password=get_password_hash("password456"),
    )
    test_session.add(user2)
    await test_session.flush()

    conv1 = Conversation(
        user_id=test_user.id,
        title="User 1 Dallas Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv1)
    await test_session.flush()
    conv1.add_message(MessageRole.USER.value, "Analyzing Dallas site")

    conv2 = Conversation(
        user_id=user2.id,
        title="User 2 Dallas Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv2)
    await test_session.flush()
    conv2.add_message(MessageRole.USER.value, "Different Dallas analysis")

    await test_session.commit()
    await test_session.refresh(conv1)
    await test_session.refresh(conv2)
    await test_session.refresh(user2)

    results_user1 = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["Dallas"],
        limit=10,
    )

    results_user2 = await search_messages_fulltext(
        test_session,
        user2.id,
        keywords=["Dallas"],
        limit=10,
    )

    conv_ids_user1 = {r.conversation_id for r in results_user1}
    conv_ids_user2 = {r.conversation_id for r in results_user2}

    assert len(conv_ids_user1.intersection(conv_ids_user2)) == 0


@pytest.mark.asyncio
async def test_search_messages_limit(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify limit parameter caps number of conversation sections returned."""
    from datetime import UTC, datetime, timedelta

    conv = Conversation(
        user_id=test_user.id,
        title="Multiple Store Mentions",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(MessageRole.USER.value, "Tell me about store location 1")
    conv.add_message(MessageRole.AGENT.value, "Store location 1 analysis")
    conv.add_message(MessageRole.USER.value, "Tell me about store location 2")
    conv.add_message(MessageRole.AGENT.value, "Store location 2 analysis")
    conv.add_message(MessageRole.USER.value, "Tell me about store location 3")

    await test_session.commit()
    await test_session.refresh(conv)

    results = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["store", "location"],
        limit=2,
    )

    assert len(results) <= 2


@pytest.mark.asyncio
async def test_search_messages_case_insensitive(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify default search ignores case when matching keywords."""
    from datetime import UTC, datetime, timedelta

    conv = Conversation(
        user_id=test_user.id,
        title="Dallas Site",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(MessageRole.USER.value, "Tell me about the Dallas location")

    await test_session.commit()
    await test_session.refresh(conv)

    results_lower = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["dallas"],
        limit=10,
    )

    results_mixed = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["Dallas"],
        limit=10,
    )

    assert len(results_lower) == len(results_mixed)
    assert len(results_lower) >= 1


@pytest.mark.asyncio
async def test_search_messages_multiple_keywords(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify multiple keywords use OR logic (match any)."""
    from datetime import UTC, datetime, timedelta

    conv1 = Conversation(
        user_id=test_user.id,
        title="Cannibalization Study",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=2),
    )
    test_session.add(conv1)
    await test_session.flush()
    conv1.add_message(MessageRole.USER.value, "Analyze cannibalization risk")

    conv2 = Conversation(
        user_id=test_user.id,
        title="Trade Area Overlap",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv2)
    await test_session.flush()
    conv2.add_message(MessageRole.USER.value, "Check overlap between stores")

    conv3 = Conversation(
        user_id=test_user.id,
        title="Infill Strategy",
        messages_document=[],
        created_at=datetime.now(UTC),
    )
    test_session.add(conv3)
    await test_session.flush()
    conv3.add_message(MessageRole.USER.value, "Review infill opportunities")

    await test_session.commit()
    await test_session.refresh(conv1)
    await test_session.refresh(conv2)
    await test_session.refresh(conv3)

    results = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["cannibalization", "overlap", "infill"],
        limit=10,
    )

    assert len(results) >= 1
    result_content = " ".join([r.matched_message.content.lower() for r in results])
    assert any(kw in result_content for kw in ["cannibalization", "overlap", "infill"])


@pytest.mark.asyncio
async def test_search_messages_no_results(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify search returns empty when no messages match keywords."""
    from datetime import UTC, datetime, timedelta

    conv = Conversation(
        user_id=test_user.id,
        title="Test Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()
    conv.add_message(MessageRole.USER.value, "Some regular content")

    await test_session.commit()
    await test_session.refresh(conv)

    results = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["nonexistent_keyword_xyz123"],
        limit=10,
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_messages_role_filter_user(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify role_filter='user' returns only user messages."""
    conv = Conversation(
        user_id=test_user.id,
        title="Mixed Role Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(
        MessageRole.USER.value, "User mentions uniqueterm_rolefilteruser here"
    )
    conv.add_message(
        MessageRole.AGENT.value, "Agent also mentions uniqueterm_rolefilteruser here"
    )
    conv.add_message(
        MessageRole.USER.value, "Another user message about uniqueterm_rolefilteruser"
    )

    await test_session.commit()
    await test_session.refresh(conv)

    results_user = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["uniqueterm_rolefilteruser"],
        limit=10,
        role_filter=MessageRole.USER.value,
    )

    assert (
        len(results_user) == 1
    ), "Should match exactly one conversation with first user message"
    assert all(
        r.matched_message.role == MessageRole.USER.value for r in results_user
    ), "All matched messages must be user messages"


@pytest.mark.asyncio
async def test_search_messages_role_filter_agent(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify role_filter='assistant' returns only agent messages."""
    conv = Conversation(
        user_id=test_user.id,
        title="Mixed Role Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(MessageRole.USER.value, "User message")
    conv.add_message(
        MessageRole.AGENT.value, "Agent mentions uniqueterm_rolefilteragent here"
    )
    conv.add_message(
        MessageRole.AGENT.value, "Second agent message with uniqueterm_rolefilteragent"
    )
    conv.add_message(MessageRole.USER.value, "Another user message")

    await test_session.commit()
    await test_session.refresh(conv)

    results_agent = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["uniqueterm_rolefilteragent"],
        limit=10,
        role_filter=MessageRole.AGENT.value,
    )

    assert (
        len(results_agent) == 1
    ), "Should match exactly one conversation with first agent message"
    assert all(
        r.matched_message.role == MessageRole.AGENT.value for r in results_agent
    ), "All matched messages must be agent messages"


@pytest.mark.asyncio
async def test_search_messages_context_at_start_of_conversation(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify context window handles match at conversation start (no messages_before)."""
    conv = Conversation(
        user_id=test_user.id,
        title="Test Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(MessageRole.USER.value, "First message with keyword match")
    conv.add_message(MessageRole.AGENT.value, "Second message")
    conv.add_message(MessageRole.USER.value, "Third message")

    await test_session.commit()
    await test_session.refresh(conv)

    results = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["match"],
        limit=10,
        context_before=5,
        context_after=2,
    )

    assert len(results) >= 1
    result = results[0]
    assert len(result.messages_before) == 0
    assert len(result.messages_after) == 2
    assert result.match_index == 0


@pytest.mark.asyncio
async def test_search_messages_context_at_end_of_conversation(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify context window handles match at conversation end (no messages_after)."""
    conv = Conversation(
        user_id=test_user.id,
        title="Test Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    test_session.add(conv)
    await test_session.flush()

    conv.add_message(MessageRole.USER.value, "First message")
    conv.add_message(MessageRole.AGENT.value, "Second message")
    conv.add_message(MessageRole.USER.value, "Last message with keyword match")

    await test_session.commit()
    await test_session.refresh(conv)

    results = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["match"],
        limit=10,
        context_before=2,
        context_after=5,
    )

    assert len(results) >= 1
    result = results[0]
    assert len(result.messages_before) == 2
    assert len(result.messages_after) == 0
    assert result.match_index == 2


@pytest.mark.asyncio
async def test_search_messages_max_days_ago_filter(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify max_days_ago filters out older conversations."""
    old_conv = Conversation(
        user_id=test_user.id,
        title="Old Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=100),
    )
    test_session.add(old_conv)
    await test_session.flush()
    old_conv.add_message(MessageRole.USER.value, "Old message with searchterm")

    recent_conv = Conversation(
        user_id=test_user.id,
        title="Recent Conversation",
        messages_document=[],
        created_at=datetime.now(UTC) - timedelta(days=5),
    )
    test_session.add(recent_conv)
    await test_session.flush()
    recent_conv.add_message(MessageRole.USER.value, "Recent message with searchterm")

    await test_session.commit()
    await test_session.refresh(old_conv)
    await test_session.refresh(recent_conv)

    results_all = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["searchterm"],
        limit=10,
    )

    results_recent = await search_messages_fulltext(
        test_session,
        test_user.id,
        keywords=["searchterm"],
        limit=10,
        max_days_ago=30,
    )

    assert len(results_all) >= 2
    assert len(results_recent) == 1
    assert results_recent[0].conversation_id == recent_conv.id


@pytest.mark.asyncio
async def test_search_messages_case_insensitive_default(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify case_sensitive=False (default) matches regardless of case."""
    conversation = Conversation(
        user_id=test_user.id,
        title="Case Test",
        messages_document=[],
    )
    test_session.add(conversation)
    await test_session.flush()
    conversation.add_message(
        MessageRole.USER.value, "The AUSTIN market looks promising"
    )
    await test_session.commit()
    await test_session.refresh(conversation)

    test_cases = [
        (["austin"], True),
        (["AUSTIN"], True),
        (["Austin"], True),
        (["AuStIn"], True),
    ]

    for keywords, should_match in test_cases:
        results = await search_messages_fulltext(
            test_session, test_user.id, keywords=keywords
        )
        if should_match:
            assert len(results) == 1, f"Should match with keywords {keywords}"
        else:
            assert len(results) == 0, f"Should not match with keywords {keywords}"
        results = await search_messages_fulltext(
            test_session, test_user.id, keywords=keywords
        )
        if should_match:
            assert len(results) == 1, f"Should match with keywords {keywords}"
        else:
            assert len(results) == 0, f"Should not match with keywords {keywords}"


@pytest.mark.asyncio
async def test_search_messages_case_sensitive_enabled(
    test_session: AsyncSession,
    test_user: User,
):
    """Verify case_sensitive=True requires exact case match."""
    conversation = Conversation(
        user_id=test_user.id,
        title="Case Test",
        messages_document=[],
    )
    test_session.add(conversation)
    await test_session.flush()
    conversation.add_message(
        MessageRole.USER.value, "The AUSTIN market looks promising"
    )
    await test_session.commit()
    await test_session.refresh(conversation)

    test_cases = [
        (["AUSTIN"], True),
        (["austin"], False),
        (["Austin"], False),
        (["AuStIn"], False),
    ]

    for keywords, should_match in test_cases:
        results = await search_messages_fulltext(
            test_session, test_user.id, keywords=keywords, case_sensitive=True
        )
        if should_match:
            assert len(results) == 1, f"Should match with keywords {keywords}"
        else:
            assert len(results) == 0, f"Should not match with keywords {keywords}"
    await test_session.flush()
    conversation.add_message(
        MessageRole.USER.value, "The AUSTIN market looks promising"
    )
    await test_session.commit()
    await test_session.refresh(conversation)

    test_cases = [
        (["AUSTIN"], True),
        (["austin"], False),
        (["Austin"], False),
        (["AuStIn"], False),
    ]

    for keywords, should_match in test_cases:
        results = await search_messages_fulltext(
            test_session, test_user.id, keywords=keywords, case_sensitive=True
        )
        if should_match:
            assert len(results) == 1, f"Should match with keywords {keywords}"
        else:
            assert len(results) == 0, f"Should not match with keywords {keywords}"
