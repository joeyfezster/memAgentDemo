from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
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

    conversation = Conversation(user_id=user.id)
    test_session.add(conversation)
    await test_session.commit()
    await test_session.refresh(conversation)

    assert conversation.id is not None
    assert conversation.user_id == user.id
    assert conversation.created_at is not None
    assert conversation.updated_at is not None


@pytest.mark.asyncio
async def test_message_model_integrity(test_session: AsyncSession):
    user = User(
        email="msg_test@example.com",
        display_name="Message Test User",
        hashed_password=get_password_hash("password123"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    conversation = Conversation(user_id=user.id)
    test_session.add(conversation)
    await test_session.commit()
    await test_session.refresh(conversation)

    test_cases = [
        (
            {
                "conversation_id": conversation.id,
                "role": MessageRole.USER,
                "content": "Hello, this is a test message",
            },
            None,
        ),
        (
            {
                "conversation_id": conversation.id,
                "role": MessageRole.AGENT,
                "content": "This is a response",
            },
            None,
        ),
    ]

    for message_data, expected_error in test_cases:
        if expected_error:
            with pytest.raises(expected_error):
                message = Message(**message_data)
                test_session.add(message)
                await test_session.commit()
        else:
            message = Message(**message_data)
            test_session.add(message)
            await test_session.commit()
            await test_session.refresh(message)

            assert message.id is not None
            assert message.conversation_id == message_data["conversation_id"]
            assert message.role == message_data["role"]
            assert message.content == message_data["content"]
            assert message.created_at is not None


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

    conversation = Conversation(user_id=user.id)
    test_session.add(conversation)
    await test_session.commit()
    await test_session.refresh(conversation)

    message = Message(
        conversation_id=conversation.id, role="user", content="Test message"
    )
    test_session.add(message)
    await test_session.commit()

    await test_session.delete(user)
    await test_session.commit()

    from sqlalchemy import select

    conv_result = await test_session.execute(
        select(Conversation).where(Conversation.id == conversation.id)
    )
    assert conv_result.scalar_one_or_none() is None

    msg_result = await test_session.execute(
        select(Message).where(Message.id == message.id)
    )
    assert msg_result.scalar_one_or_none() is None


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

    required_columns = {"id", "user_id", "title", "created_at", "updated_at"}

    assert (
        required_columns == column_names
    ), f"Missing columns: {required_columns - column_names}, Extra columns: {column_names - required_columns}"


@pytest.mark.asyncio
async def test_message_model_columns():
    inspector = inspect(Message)
    column_names = {col.name for col in inspector.columns}

    required_columns = {"id", "conversation_id", "role", "content", "created_at"}

    assert (
        required_columns == column_names
    ), f"Missing columns: {required_columns - column_names}, Extra columns: {column_names - required_columns}"
