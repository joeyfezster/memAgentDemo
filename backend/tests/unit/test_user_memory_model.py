"""Unit tests for User model memory document methods"""

import pytest

from app.models.user import User
from app.models.types import MemoryDocument, PlacerPOI


@pytest.mark.asyncio
async def test_user_get_memory_empty():
    """Verify get_memory returns initialized MemoryDocument when empty"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    memory = user.get_memory()

    assert isinstance(memory, MemoryDocument)
    assert len(memory.facts) == 0
    assert len(memory.placer_user_datapoints) == 0
    assert memory.metadata.total_facts == 0
    assert memory.metadata.total_active_facts == 0
    assert memory.metadata.total_pois == 0


@pytest.mark.asyncio
async def test_user_add_fact():
    """Verify add_fact creates and stores new fact"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    fact_id = user.add_fact(
        content="User prefers morning meetings",
        source_conversation_id="conv-123",
        source_message_id="msg-456",
    )

    assert isinstance(fact_id, str)
    assert len(fact_id) == 36

    memory = user.get_memory()
    assert len(memory.facts) == 1
    assert memory.facts[0].id == fact_id
    assert memory.facts[0].content == "User prefers morning meetings"
    assert memory.facts[0].source_conversation_id == "conv-123"
    assert memory.facts[0].source_message_id == "msg-456"
    assert memory.facts[0].is_active is True
    assert memory.metadata.total_facts == 1
    assert memory.metadata.total_active_facts == 1


@pytest.mark.asyncio
async def test_user_add_multiple_facts():
    """Verify multiple facts can be added and metadata updates"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    user.add_fact("User likes coffee", None, None)
    user.add_fact("User lives in Seattle", None, None)
    user.add_fact("User works in tech", None, None)

    memory = user.get_memory()
    assert len(memory.facts) == 3
    assert memory.metadata.total_facts == 3
    assert memory.metadata.total_active_facts == 3
    assert all(f.is_active for f in memory.facts)


@pytest.mark.asyncio
async def test_user_deactivate_fact():
    """Verify deactivate_fact marks fact as inactive"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    fact_id = user.add_fact("Temporary fact", None, None)
    memory_before = user.get_memory()
    assert memory_before.facts[0].is_active is True

    success = user.deactivate_fact(fact_id)

    assert success is True
    memory_after = user.get_memory()
    assert len(memory_after.facts) == 1
    assert memory_after.facts[0].is_active is False
    assert memory_after.metadata.total_facts == 1
    assert memory_after.metadata.total_active_facts == 0


@pytest.mark.asyncio
async def test_user_deactivate_nonexistent_fact():
    """Verify deactivate_fact returns False for nonexistent fact"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    user.add_fact("Some fact", None, None)
    success = user.deactivate_fact("nonexistent-uuid")

    assert success is False
    memory = user.get_memory()
    assert memory.metadata.total_active_facts == 1


@pytest.mark.asyncio
async def test_user_get_active_facts():
    """Verify get_active_facts filters inactive facts"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    fact_id_1 = user.add_fact("Active fact 1", None, None)
    fact_id_2 = user.add_fact("Will be inactive", None, None)
    fact_id_3 = user.add_fact("Active fact 2", None, None)

    user.deactivate_fact(fact_id_2)

    active_facts = user.get_active_facts()

    assert len(active_facts) == 2
    assert all(f.is_active for f in active_facts)
    assert fact_id_1 in [f.id for f in active_facts]
    assert fact_id_3 in [f.id for f in active_facts]
    assert fact_id_2 not in [f.id for f in active_facts]


@pytest.mark.asyncio
async def test_user_add_poi():
    """Verify add_poi creates POI with initial mention"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    place_id = user.add_poi(
        place_id="place-123",
        place_name="Home Office",
        notes="Where I work from",
        conversation_id="conv-1",
        message_id="msg-1",
    )

    assert place_id == "place-123"

    memory = user.get_memory()
    assert len(memory.placer_user_datapoints) == 1
    poi = memory.placer_user_datapoints[0]
    assert isinstance(poi, PlacerPOI)
    assert poi.place_id == "place-123"
    assert poi.place_name == "Home Office"
    assert poi.notes == "Where I work from"
    assert "conv-1" in poi.mentioned_in
    assert len(poi.mentioned_in["conv-1"]) == 1
    assert poi.mentioned_in["conv-1"][0][0] == "msg-1"
    assert memory.metadata.total_pois == 1


@pytest.mark.asyncio
async def test_user_add_poi_mention():
    """Verify add_poi_mention adds mention to existing POI"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    user.add_poi("place-123", "Coffee Shop", None, "conv-1", "msg-1")
    success = user.add_poi_mention("place-123", "conv-2", "msg-2")

    assert success is True

    memory = user.get_memory()
    poi = memory.placer_user_datapoints[0]
    assert len(poi.mentioned_in) == 2
    assert "conv-1" in poi.mentioned_in
    assert "conv-2" in poi.mentioned_in
    assert len(poi.mentioned_in["conv-2"]) == 1


@pytest.mark.asyncio
async def test_user_add_poi_mention_same_conversation():
    """Verify add_poi_mention adds multiple mentions in same conversation"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    user.add_poi("place-123", "Restaurant", None, "conv-1", "msg-1")
    user.add_poi_mention("place-123", "conv-1", "msg-5")
    user.add_poi_mention("place-123", "conv-1", "msg-10")

    memory = user.get_memory()
    poi = memory.placer_user_datapoints[0]
    assert len(poi.mentioned_in["conv-1"]) == 3


@pytest.mark.asyncio
async def test_user_add_poi_mention_nonexistent():
    """Verify add_poi_mention returns False for nonexistent POI"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    success = user.add_poi_mention("nonexistent-place", "conv-1", "msg-1")

    assert success is False


@pytest.mark.asyncio
async def test_user_metadata_token_count():
    """Verify metadata includes token count"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    user.add_fact("Short fact", None, None)

    memory = user.get_memory()
    assert memory.metadata.token_count > 0


@pytest.mark.asyncio
async def test_user_immutable_update_pattern():
    """Verify updates use immutable pattern and preserve existing data"""
    user = User(
        email="test@example.com",
        display_name="Test User",
        role="user",
        hashed_password="fake_hash",
    )

    fact_id_1 = user.add_fact("First fact", None, None)

    fact_id_2 = user.add_fact("Second fact", None, None)
    updated_memory = user.get_memory()

    assert len(updated_memory.facts) == 2
    assert updated_memory.facts[0].id == fact_id_1
    assert updated_memory.facts[1].id == fact_id_2
    assert updated_memory.facts[0].content == "First fact"
    assert updated_memory.facts[1].content == "Second fact"
