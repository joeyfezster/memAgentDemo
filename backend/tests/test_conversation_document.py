from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.crud import conversation as conversation_crud
from app.db.base import Base
from app.models.conversation import Conversation
from app.models.types import MessageRole
from app.models.user import User
from app.core.security import get_password_hash


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


@pytest.mark.asyncio
async def test_create_conversation_with_empty_messages_document(
    test_session: AsyncSession, test_user: User
):
    conversation = await conversation_crud.create_conversation(
        test_session, user_id=test_user.id
    )

    assert conversation.id is not None
    assert conversation.user_id == test_user.id
    assert conversation.messages_document == []
    assert conversation.get_message_count() == 0


@pytest.mark.asyncio
async def test_add_message_to_conversation(test_session: AsyncSession, test_user: User):
    conversation = await conversation_crud.create_conversation(
        test_session, user_id=test_user.id
    )

    message = await conversation_crud.add_message_to_conversation(
        test_session,
        conversation_id=conversation.id,
        role=MessageRole.USER.value,
        content="Hello, world!",
    )

    assert message.id is not None
    assert message.role == MessageRole.USER.value
    assert message.content == "Hello, world!"
    assert message.created_at is not None

    await test_session.refresh(conversation)
    assert conversation.get_message_count() == 1


@pytest.mark.asyncio
async def test_get_conversation_messages(test_session: AsyncSession, test_user: User):
    conversation = await conversation_crud.create_conversation(
        test_session, user_id=test_user.id
    )

    test_messages = [
        (MessageRole.USER.value, "First message"),
        (MessageRole.AGENT.value, "First response"),
        (MessageRole.USER.value, "Second message"),
    ]

    for role, content in test_messages:
        await conversation_crud.add_message_to_conversation(
            test_session, conversation_id=conversation.id, role=role, content=content
        )

    retrieved_messages = await conversation_crud.get_conversation_messages(
        test_session, conversation.id
    )

    assert len(retrieved_messages) == len(test_messages)
    for i, (expected_role, expected_content) in enumerate(test_messages):
        assert retrieved_messages[i].role == expected_role
        assert retrieved_messages[i].content == expected_content


@pytest.mark.asyncio
async def test_message_ordering_preserved(test_session: AsyncSession, test_user: User):
    conversation = await conversation_crud.create_conversation(
        test_session, user_id=test_user.id
    )

    messages_to_add = [
        (MessageRole.USER.value, "Message 1"),
        (MessageRole.AGENT.value, "Response 1"),
        (MessageRole.USER.value, "Message 2"),
        (MessageRole.AGENT.value, "Response 2"),
        (MessageRole.USER.value, "Message 3"),
    ]

    for role, content in messages_to_add:
        await conversation_crud.add_message_to_conversation(
            test_session, conversation_id=conversation.id, role=role, content=content
        )

    messages = await conversation_crud.get_conversation_messages(
        test_session, conversation.id
    )

    assert len(messages) == len(messages_to_add)
    for i, (expected_role, expected_content) in enumerate(messages_to_add):
        assert messages[i].role == expected_role
        assert messages[i].content == expected_content


@pytest.mark.asyncio
async def test_conversation_with_special_characters(
    test_session: AsyncSession, test_user: User
):
    conversation = await conversation_crud.create_conversation(
        test_session, user_id=test_user.id
    )

    special_content = "Test with \"quotes\", 'apostrophes', and\nnewlines\t\ttabs\nunicode: üñîçødé;    😊"
    message = await conversation_crud.add_message_to_conversation(
        test_session,
        conversation_id=conversation.id,
        role=MessageRole.USER.value,
        content=special_content,
    )

    assert message.content == special_content

    messages = await conversation_crud.get_conversation_messages(
        test_session, conversation.id
    )
    assert messages[0].content == special_content


@pytest.mark.asyncio
async def test_user_isolation(test_session: AsyncSession, test_user: User):
    user2 = User(
        email="user2@example.com",
        display_name="User 2",
        hashed_password=get_password_hash("password456"),
    )
    test_session.add(user2)
    await test_session.commit()
    await test_session.refresh(user2)

    conv1 = await conversation_crud.create_conversation(
        test_session, user_id=test_user.id
    )
    conv2 = await conversation_crud.create_conversation(test_session, user_id=user2.id)

    await conversation_crud.add_message_to_conversation(
        test_session,
        conversation_id=conv1.id,
        role=MessageRole.USER.value,
        content="User 1 message",
    )
    await conversation_crud.add_message_to_conversation(
        test_session,
        conversation_id=conv2.id,
        role=MessageRole.USER.value,
        content="User 2 message",
    )

    result = await conversation_crud.get_conversation_by_id(
        test_session, conv2.id, test_user.id
    )
    assert result is None

    result = await conversation_crud.get_conversation_by_id(
        test_session, conv1.id, test_user.id
    )
    assert result is not None
    assert result.id == conv1.id


@pytest.mark.asyncio
async def test_cascade_delete_removes_conversations(test_session: AsyncSession):
    user = User(
        email="cascade@example.com",
        display_name="Cascade User",
        hashed_password=get_password_hash("password123"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    conversation = await conversation_crud.create_conversation(
        test_session, user_id=user.id
    )
    await conversation_crud.add_message_to_conversation(
        test_session,
        conversation_id=conversation.id,
        role=MessageRole.USER.value,
        content="Test message",
    )

    await test_session.delete(user)
    await test_session.commit()

    from sqlalchemy import select

    result = await test_session.execute(
        select(Conversation).where(Conversation.id == conversation.id)
    )
    assert result.scalar_one_or_none() is None
