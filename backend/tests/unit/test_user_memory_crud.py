"""Unit tests for user memory CRUD operations"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import (
    add_user_memory_fact,
    add_user_memory_poi,
    create_user,
    deactivate_user_memory_fact,
    get_user_memory,
)
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_add_user_memory_fact(session: AsyncSession):
    """Verify add_user_memory_fact creates and persists fact"""
    user = await create_user(
        session,
        email="memtest1@example.com",
        display_name="Memory Test User 1",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    fact_id = await add_user_memory_fact(
        session=session,
        user_id=user.id,
        content="User loves hiking",
        source_conversation_id="conv-abc",
        source_message_id="msg-123",
    )

    assert isinstance(fact_id, str)
    assert len(fact_id) == 36

    memory = await get_user_memory(session, user.id)
    assert len(memory.facts) == 1
    assert memory.facts[0].content == "User loves hiking"
    assert memory.facts[0].source_conversation_id == "conv-abc"


@pytest.mark.asyncio
async def test_add_user_memory_fact_nonexistent_user(session: AsyncSession):
    """Verify add_user_memory_fact raises error for nonexistent user"""
    with pytest.raises(ValueError, match="User .* not found"):
        await add_user_memory_fact(
            session=session,
            user_id="nonexistent-user-id",
            content="Some fact",
            source_conversation_id=None,
            source_message_id=None,
        )


@pytest.mark.asyncio
async def test_deactivate_user_memory_fact(session: AsyncSession):
    """Verify deactivate_user_memory_fact marks fact as inactive"""
    user = await create_user(
        session,
        email="memtest2@example.com",
        display_name="Memory Test User 2",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    fact_id = await add_user_memory_fact(
        session, user.id, "Temporary preference", None, None
    )

    success = await deactivate_user_memory_fact(session, user.id, fact_id)

    assert success is True

    memory = await get_user_memory(session, user.id)
    assert memory.facts[0].is_active is False
    assert memory.metadata.total_active_facts == 0


@pytest.mark.asyncio
async def test_deactivate_user_memory_fact_nonexistent(session: AsyncSession):
    """Verify deactivate_user_memory_fact returns False for nonexistent fact"""
    user = await create_user(
        session,
        email="memtest3@example.com",
        display_name="Memory Test User 3",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    success = await deactivate_user_memory_fact(session, user.id, "fake-fact-id")

    assert success is False


@pytest.mark.asyncio
async def test_deactivate_user_memory_fact_nonexistent_user(session: AsyncSession):
    """Verify deactivate_user_memory_fact raises error for nonexistent user"""
    with pytest.raises(ValueError, match="User .* not found"):
        await deactivate_user_memory_fact(
            session, "nonexistent-user-id", "some-fact-id"
        )


@pytest.mark.asyncio
async def test_add_user_memory_poi(session: AsyncSession):
    """Verify add_user_memory_poi creates and persists POI"""
    user = await create_user(
        session,
        email="memtest4@example.com",
        display_name="Memory Test User 4",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    poi_id = await add_user_memory_poi(
        session=session,
        user_id=user.id,
        place_id="poi-789",
        place_name="Favorite Coffee Shop",
        notes="Great latte",
        conversation_id="conv-xyz",
        message_id="msg-456",
    )

    assert poi_id == "poi-789"

    memory = await get_user_memory(session, user.id)
    assert len(memory.placer_user_datapoints) == 1
    poi = memory.placer_user_datapoints[0]
    assert poi.place_id == "poi-789"
    assert poi.place_name == "Favorite Coffee Shop"
    assert poi.notes == "Great latte"


@pytest.mark.asyncio
async def test_add_user_memory_poi_nonexistent_user(session: AsyncSession):
    """Verify add_user_memory_poi raises error for nonexistent user"""
    with pytest.raises(ValueError, match="User .* not found"):
        await add_user_memory_poi(
            session=session,
            user_id="nonexistent-user-id",
            place_id="poi-123",
            place_name="Some Place",
            notes=None,
            conversation_id="conv-1",
            message_id="msg-1",
        )


@pytest.mark.asyncio
async def test_get_user_memory_empty(session: AsyncSession):
    """Verify get_user_memory returns empty memory for new user"""
    user = await create_user(
        session,
        email="memtest5@example.com",
        display_name="Memory Test User 5",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    memory = await get_user_memory(session, user.id)

    assert len(memory.facts) == 0
    assert len(memory.placer_user_datapoints) == 0
    assert memory.metadata.total_facts == 0
    assert memory.metadata.total_pois == 0


@pytest.mark.asyncio
async def test_get_user_memory_nonexistent_user(session: AsyncSession):
    """Verify get_user_memory raises error for nonexistent user"""
    with pytest.raises(ValueError, match="User .* not found"):
        await get_user_memory(session, "nonexistent-user-id")


@pytest.mark.asyncio
async def test_user_isolation(session: AsyncSession):
    """Verify user memories are isolated from each other"""
    user1 = await create_user(
        session,
        email="memtest6@example.com",
        display_name="Memory Test User 6",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    user2 = await create_user(
        session,
        email="memtest7@example.com",
        display_name="Memory Test User 7",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    await add_user_memory_fact(session, user1.id, "User 1 fact", None, None)
    await add_user_memory_fact(session, user2.id, "User 2 fact", None, None)

    memory1 = await get_user_memory(session, user1.id)
    memory2 = await get_user_memory(session, user2.id)

    assert len(memory1.facts) == 1
    assert len(memory2.facts) == 1
    assert memory1.facts[0].content == "User 1 fact"
    assert memory2.facts[0].content == "User 2 fact"


@pytest.mark.asyncio
async def test_multiple_operations_on_same_user(session: AsyncSession):
    """Verify multiple memory operations work correctly on same user"""
    user = await create_user(
        session,
        email="memtest8@example.com",
        display_name="Memory Test User 8",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    fact_id_1 = await add_user_memory_fact(session, user.id, "Fact 1", None, None)
    fact_id_2 = await add_user_memory_fact(session, user.id, "Fact 2", None, None)
    await add_user_memory_poi(
        session, user.id, "poi-1", "Place 1", None, "conv-1", "msg-1"
    )

    await deactivate_user_memory_fact(session, user.id, fact_id_1)

    memory = await get_user_memory(session, user.id)

    assert memory.metadata.total_facts == 2
    assert memory.metadata.total_active_facts == 1
    assert memory.metadata.total_pois == 1

    active_facts = [f for f in memory.facts if f.is_active]
    assert len(active_facts) == 1
    assert active_facts[0].id == fact_id_2
