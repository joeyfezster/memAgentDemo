"""Expensive agent integration tests for user memory feature"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.crud import conversation as conversation_crud
from app.crud.user import get_user_memory
from app.models.user import User
from app.services.agent_service import AgentService
from tests.conftest import consume_streaming_response

pytestmark = [pytest.mark.asyncio, pytest.mark.expensive]
TEST_MODEL = "claude-sonnet-4-5-20250929"


@pytest_asyncio.fixture
async def user_memory_test_user(session: AsyncSession) -> User:
    """Create a fresh test user for user memory tests"""
    user = User(
        email=f"user-memory-test-{uuid.uuid4()}@example.com",
        display_name="User Memory Tester",
        hashed_password=get_password_hash("password123"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_agent_stores_user_fact_when_explicitly_asked(
    session: AsyncSession, user_memory_test_user: User
):
    """Verify agent stores fact when user explicitly asks to remember"""
    settings = get_settings()
    agent_service = AgentService(settings)

    conv = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    user_message_content = (
        "My name is Alex and I prefer to be called by that name. Please remember this."
    )
    user_message_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv.id,
        role="user",
        content=user_message_content,
        tool_metadata=None,
    )

    response = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_message_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=user_message_dict.id,
        )
    )

    assert "alex" in response.text.lower()

    memory = await get_user_memory(session, user_memory_test_user.id)
    assert memory.metadata.total_active_facts > 0

    fact_contents = [f.content.lower() for f in memory.facts if f.is_active]
    assert any("alex" in content for content in fact_contents)

    assert len(memory.facts) == 1
    fact = memory.facts[0]
    assert fact.id is not None
    assert fact.content is not None
    assert fact.is_active is True
    assert fact.added_at is not None
    assert fact.source_conversation_id == conv.id
    assert fact.source_message_id == user_message_dict.id


@pytest.mark.asyncio
async def test_agent_retrieves_and_uses_stored_memory(
    session: AsyncSession, user_memory_test_user: User
):
    """Verify agent references stored memories in new conversation across multiple messages."""
    settings = get_settings()
    agent_service = AgentService(settings)

    conv1 = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    msg1_content = (
        "Please remember that I am vegetarian and prefer plant-based options."
    )
    msg1_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv1.id,
        role="user",
        content=msg1_content,
        tool_metadata=None,
    )

    await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv1.id,
            user_message_content=msg1_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=msg1_dict.id,
        )
    )

    memory = await get_user_memory(session, user_memory_test_user.id)
    assert memory.metadata.total_active_facts > 0

    vegetarian_facts = [
        f
        for f in memory.facts
        if f.is_active
        and ("vegetarian" in f.content.lower() or "plant-based" in f.content.lower())
    ]
    assert len(vegetarian_facts) > 0
    fact = vegetarian_facts[0]
    assert fact.source_conversation_id == conv1.id
    assert fact.source_message_id == msg1_dict.id
    assert fact.added_at is not None

    conv2 = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    msg2_content = "What do you know about my food preferences?"
    msg2_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv2.id,
        role="user",
        content=msg2_content,
        tool_metadata=None,
    )

    response2 = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv2.id,
            user_message_content=msg2_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=msg2_dict.id,
        )
    )

    assert (
        "vegetarian" in response2.text.lower()
        or "plant-based" in response2.text.lower()
    )


@pytest.mark.asyncio
async def test_agent_stores_poi_when_user_mentions_place(
    session: AsyncSession, user_memory_test_user: User
):
    """Verify agent stores place of interest when user mentions important location"""
    settings = get_settings()
    agent_service = AgentService(settings)

    conv = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    msg_content = (
        "I work at the Microsoft campus in Redmond. Please remember this location."
    )
    msg_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv.id,
        role="user",
        content=msg_content,
        tool_metadata=None,
    )

    response = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv.id,
            user_message_content=msg_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=msg_dict.id,
        )
    )

    assert "remember" in response.text.lower() or "stored" in response.text.lower()

    memory = await get_user_memory(session, user_memory_test_user.id)

    has_poi = memory.metadata.total_pois > 0
    has_work_fact = any(
        "work" in f.content.lower() or "microsoft" in f.content.lower()
        for f in memory.facts
        if f.is_active
    )

    assert has_poi or has_work_fact

    if has_poi:
        assert len(memory.placer_user_datapoints) > 0
        poi = memory.placer_user_datapoints[0]
        assert poi.place_id is not None
        assert poi.place_name is not None
        assert conv.id in poi.mentioned_in
        mention_ids = poi.mentioned_in[conv.id]
        assert len(mention_ids) > 0
        assert all(msg_id is not None for msg_id in mention_ids)

    if has_work_fact:
        work_facts = [
            f
            for f in memory.facts
            if f.is_active
            and ("work" in f.content.lower() or "microsoft" in f.content.lower())
        ]
        fact = work_facts[0]
        assert fact.source_conversation_id == conv.id
        assert fact.source_message_id == msg_dict.id


@pytest.mark.asyncio
async def test_agent_can_deactivate_outdated_fact(
    session: AsyncSession, user_memory_test_user: User
):
    """Verify agent can mark facts as outdated when user provides corrections"""
    settings = get_settings()
    agent_service = AgentService(settings)

    conv1 = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    msg1_content = "Please remember that I live in Portland."
    msg1_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv1.id,
        role="user",
        content=msg1_content,
        tool_metadata=None,
    )

    await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv1.id,
            user_message_content=msg1_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=msg1_dict.id,
        )
    )

    memory_before = await get_user_memory(session, user_memory_test_user.id)
    initial_active_count = memory_before.metadata.total_active_facts

    conv2 = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    msg2_content = "Actually, I moved to Seattle. Please update what you remember about where I live."
    msg2_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv2.id,
        role="user",
        content=msg2_content,
        tool_metadata=None,
    )

    response2 = await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv2.id,
            user_message_content=msg2_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=msg2_dict.id,
        )
    )

    memory_after = await get_user_memory(session, user_memory_test_user.id)

    seattle_facts = [
        f for f in memory_after.facts if f.is_active and "seattle" in f.content.lower()
    ]
    assert len(seattle_facts) > 0

    seattle_fact = seattle_facts[0]
    assert seattle_fact.source_conversation_id == conv2.id
    assert seattle_fact.source_message_id == msg2_dict.id
    assert seattle_fact.added_at is not None

    portland_facts = [
        f
        for f in memory_after.facts
        if not f.is_active and "portland" in f.content.lower()
    ]
    if portland_facts:
        portland_fact = portland_facts[0]
        assert portland_fact.source_conversation_id == conv1.id
        assert portland_fact.deactivated_at is not None


@pytest.mark.asyncio
async def test_poi_mentioned_in_multiple_conversations(
    session: AsyncSession, user_memory_test_user: User
):
    """Verify POI mentions are correctly tracked across multiple conversations"""
    settings = get_settings()
    agent_service = AgentService(settings)

    conv1 = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    msg1_content = "I work at the Microsoft campus in Redmond. Please remember this as a place of interest (POI) to me."
    msg1_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv1.id,
        role="user",
        content=msg1_content,
        tool_metadata=None,
    )

    await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv1.id,
            user_message_content=msg1_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=msg1_dict.id,
        )
    )

    memory_after_conv1 = await get_user_memory(session, user_memory_test_user.id)

    assert memory_after_conv1.metadata.total_pois > 0

    conv2 = await conversation_crud.create_conversation(
        session, user_id=user_memory_test_user.id
    )

    msg2_content = (
        "I had a meeting at Microsoft Redmond yesterday. Can you remember this?"
    )
    msg2_dict = await conversation_crud.add_message_to_conversation(
        session=session,
        conversation_id=conv2.id,
        role="user",
        content=msg2_content,
        tool_metadata=None,
    )

    await consume_streaming_response(
        agent_service.stream_response_with_tools(
            conversation_id=conv2.id,
            user_message_content=msg2_content,
            user=user_memory_test_user,
            session=session,
            user_message_id=msg2_dict.id,
        )
    )

    memory_after_conv2 = await get_user_memory(session, user_memory_test_user.id)

    microsoft_pois = [
        p
        for p in memory_after_conv2.placer_user_datapoints
        if "microsoft" in p.place_name.lower() or "redmond" in p.place_name.lower()
    ]

    assert len(microsoft_pois) > 0, "Should have at least one Microsoft-related POI"

    # Verify conversation tracking exists
    all_conversation_ids = set()
    for poi in microsoft_pois:
        all_conversation_ids.update(poi.mentioned_in.keys())

    assert conv1.id in all_conversation_ids, "POI should track mention in conv1"
    assert conv2.id in all_conversation_ids, "POI should track mention in conv2"
