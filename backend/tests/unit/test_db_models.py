from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_engine, get_session_factory, init_engine
from app.models.user import User
from app.models.conversation import Conversation
from app.models.types import MessageRole
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_session():
    init_engine()
    engine = get_engine()
    session_factory = get_session_factory()

    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_model_integrity(test_session: AsyncSession):
    test_cases = [
        (
            {
                "email": "test@example.com",
                "display_name": "Test User",
                "role": "analyst",
                "hashed_password": get_password_hash("password123"),
            },
            None,
        ),
        (
            {
                "email": "test2@example.com",
                "display_name": "Test User 2",
                "role": None,
                "hashed_password": get_password_hash("password123"),
            },
            None,
        ),
    ]

    for user_data, expected_error in test_cases:
        if expected_error:
            with pytest.raises(expected_error):
                user = User(**user_data)
                test_session.add(user)
                await test_session.commit()
        else:
            user = User(**user_data)
            test_session.add(user)
            await test_session.commit()
            await test_session.refresh(user)

            assert user.id is not None
            assert user.email == user_data["email"]
            assert user.display_name == user_data["display_name"]
            assert user.role == user_data["role"]
            assert user.hashed_password == user_data["hashed_password"]
            assert user.created_at is not None
            assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_email_uniqueness(test_session: AsyncSession):
    user1 = User(
        email="unique@example.com",
        display_name="User 1",
        hashed_password=get_password_hash("password123"),
    )
    test_session.add(user1)
    await test_session.commit()

    user2 = User(
        email="unique@example.com",
        display_name="User 2",
        hashed_password=get_password_hash("password456"),
    )
    test_session.add(user2)

    with pytest.raises(Exception):
        await test_session.commit()


@pytest.mark.asyncio
async def test_conversation_model_integrity(test_session: AsyncSession):
    user = User(
        email="conv_test@example.com",
        display_name="Conversation Test User",
        hashed_password=get_password_hash("password123"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    conversation = Conversation(user_id=user.id, messages_document=[])
    test_session.add(conversation)
    await test_session.commit()
    await test_session.refresh(conversation)

    assert conversation.id is not None
    assert conversation.user_id == user.id
    assert conversation.created_at is not None
    assert conversation.updated_at is not None
    assert conversation.messages_document == []


@pytest.mark.asyncio
async def test_conversation_with_messages(test_session: AsyncSession):
    user = User(
        email="msg_test@example.com",
        display_name="Message Test User",
        hashed_password=get_password_hash("password123"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    conversation = Conversation(user_id=user.id, messages_document=[])
    test_session.add(conversation)
    await test_session.commit()
    await test_session.refresh(conversation)

    messages_to_send = [
        (MessageRole.USER.value, "Hello, this is a test message"),
        (MessageRole.AGENT.value, "This is a response"),
    ]

    for role, content in messages_to_send:
        message = conversation.add_message(role, content)
        assert message.id is not None
        assert message.role == role
        assert message.content == content
        assert message.created_at is not None

    await test_session.commit()
    await test_session.refresh(conversation)

    messages = conversation.get_messages()
    assert len(messages) == len(messages_to_send)
    for i, (expected_role, expected_content) in enumerate(messages_to_send):
        assert messages[i].role == expected_role
        assert messages[i].content == expected_content


@pytest.mark.asyncio
async def test_cascade_delete(test_session: AsyncSession):
    user = User(
        email="cascade@example.com",
        display_name="Cascade Test User",
        hashed_password=get_password_hash("password123"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    conversation = Conversation(user_id=user.id, messages_document=[])
    test_session.add(conversation)
    await test_session.commit()
    await test_session.refresh(conversation)

    conversation.add_message(MessageRole.USER.value, "Test message")
    await test_session.commit()

    await test_session.delete(user)
    await test_session.commit()

    from sqlalchemy import select

    conv_result = await test_session.execute(
        select(Conversation).where(Conversation.id == conversation.id)
    )
    assert conv_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_user_model_columns():
    inspector = inspect(User)
    column_names = {col.name for col in inspector.columns}

    required_columns = {
        "id",
        "email",
        "display_name",
        "role",
        "hashed_password",
        "created_at",
        "updated_at",
    }

    assert (
        required_columns == column_names
    ), f"Missing columns: {required_columns - column_names}, Extra columns: {column_names - required_columns}"


@pytest.mark.asyncio
async def test_conversation_model_columns():
    inspector = inspect(Conversation)
    column_names = {col.name for col in inspector.columns}

    required_columns = {
        "id",
        "user_id",
        "title",
        "messages_document",
        "embedding",
        "created_at",
        "updated_at",
    }

    assert (
        required_columns == column_names
    ), f"Missing columns: {required_columns - column_names}, Extra columns: {column_names - required_columns}"
