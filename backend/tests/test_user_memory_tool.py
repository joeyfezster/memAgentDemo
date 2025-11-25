"""Tests for ManageUserMemoryTool"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.user_memory_tools import ManageUserMemoryTool
from app.core.security import get_password_hash
from app.crud.user import create_user


@pytest.mark.asyncio
async def test_tool_add_fact(session: AsyncSession):
    """Verify tool can add a fact"""
    user = await create_user(
        session,
        email="tooltest1@example.com",
        display_name="Tool Test User 1",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-123",
        message_id="msg-456",
        operation="add_fact",
        content="User prefers tea over coffee",
    )

    assert result["success"] is True
    assert result["operation"] == "add_fact"
    assert "fact_id" in result
    assert "User prefers tea over coffee" in result["message"]


@pytest.mark.asyncio
async def test_tool_add_fact_missing_content(session: AsyncSession):
    """Verify tool validates required content parameter"""
    user = await create_user(
        session,
        email="tooltest2@example.com",
        display_name="Tool Test User 2",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-123",
        message_id="msg-456",
        operation="add_fact",
    )

    assert result["success"] is False
    assert "content is required" in result["error"]


@pytest.mark.asyncio
async def test_tool_deactivate_fact(session: AsyncSession):
    """Verify tool can deactivate a fact"""
    user = await create_user(
        session,
        email="tooltest3@example.com",
        display_name="Tool Test User 3",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()

    add_result = await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-123",
        message_id="msg-456",
        operation="add_fact",
        content="Old preference",
    )
    fact_id = add_result["fact_id"]

    deactivate_result = await tool.execute(
        session=session,
        user_id=user.id,
        operation="deactivate_fact",
        fact_id=fact_id,
    )

    assert deactivate_result["success"] is True
    assert deactivate_result["operation"] == "deactivate_fact"
    assert fact_id in deactivate_result["message"]


@pytest.mark.asyncio
async def test_tool_deactivate_fact_missing_fact_id(session: AsyncSession):
    """Verify tool validates required fact_id parameter"""
    user = await create_user(
        session,
        email="tooltest4@example.com",
        display_name="Tool Test User 4",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        operation="deactivate_fact",
    )

    assert result["success"] is False
    assert "fact_id is required" in result["error"]


@pytest.mark.asyncio
async def test_tool_deactivate_nonexistent_fact(session: AsyncSession):
    """Verify tool handles nonexistent fact gracefully"""
    user = await create_user(
        session,
        email="tooltest5@example.com",
        display_name="Tool Test User 5",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        operation="deactivate_fact",
        fact_id="nonexistent-fact-id",
    )

    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_tool_add_poi(session: AsyncSession):
    """Verify tool can add a POI"""
    user = await create_user(
        session,
        email="tooltest6@example.com",
        display_name="Tool Test User 6",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-123",
        message_id="msg-456",
        operation="add_poi",
        place_id="poi-789",
        place_name="User's Favorite Park",
        notes="Great for running",
    )

    assert result["success"] is True
    assert result["operation"] == "add_poi"
    assert result["place_id"] == "poi-789"
    assert "User's Favorite Park" in result["message"]


@pytest.mark.asyncio
async def test_tool_add_poi_missing_required_fields(session: AsyncSession):
    """Verify tool validates required POI parameters"""
    user = await create_user(
        session,
        email="tooltest7@example.com",
        display_name="Tool Test User 7",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-123",
        message_id="msg-456",
        operation="add_poi",
        place_id="poi-123",
    )

    assert result["success"] is False
    assert "place_name are required" in result["error"]


@pytest.mark.asyncio
async def test_tool_get_memory_empty(session: AsyncSession):
    """Verify tool can retrieve empty memory"""
    user = await create_user(
        session,
        email="tooltest8@example.com",
        display_name="Tool Test User 8",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        operation="get_memory",
    )

    assert result["success"] is True
    assert result["operation"] == "get_memory"
    assert len(result["facts"]) == 0
    assert len(result["places"]) == 0
    assert result["metadata"]["total_facts"] == 0
    assert result["metadata"]["total_pois"] == 0


@pytest.mark.asyncio
async def test_tool_get_memory_with_data(session: AsyncSession):
    """Verify tool retrieves stored facts and POIs"""
    user = await create_user(
        session,
        email="tooltest9@example.com",
        display_name="Tool Test User 9",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()

    await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-1",
        message_id="msg-1",
        operation="add_fact",
        content="User is vegetarian",
    )

    await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-1",
        message_id="msg-2",
        operation="add_poi",
        place_id="poi-1",
        place_name="Veggie Restaurant",
        notes="Best salads",
    )

    result = await tool.execute(
        session=session,
        user_id=user.id,
        operation="get_memory",
    )

    assert result["success"] is True
    assert len(result["facts"]) == 1
    assert result["facts"][0]["content"] == "User is vegetarian"
    assert len(result["places"]) == 1
    assert result["places"][0]["place_name"] == "Veggie Restaurant"
    assert result["metadata"]["total_active_facts"] == 1
    assert result["metadata"]["total_pois"] == 1


@pytest.mark.asyncio
async def test_tool_get_memory_filters_inactive_facts(session: AsyncSession):
    """Verify get_memory only returns active facts"""
    user = await create_user(
        session,
        email="tooltest10@example.com",
        display_name="Tool Test User 10",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()

    add_result = await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-1",
        message_id="msg-1",
        operation="add_fact",
        content="Inactive fact",
    )
    fact_id = add_result["fact_id"]

    await tool.execute(
        session=session,
        user_id=user.id,
        conversation_id="conv-1",
        message_id="msg-2",
        operation="add_fact",
        content="Active fact",
    )

    await tool.execute(
        session=session,
        user_id=user.id,
        operation="deactivate_fact",
        fact_id=fact_id,
    )

    result = await tool.execute(
        session=session,
        user_id=user.id,
        operation="get_memory",
    )

    assert len(result["facts"]) == 1
    assert result["facts"][0]["content"] == "Active fact"
    assert result["metadata"]["total_facts"] == 2
    assert result["metadata"]["total_active_facts"] == 1


@pytest.mark.asyncio
async def test_tool_no_session():
    """Verify tool handles missing session gracefully"""
    tool = ManageUserMemoryTool()
    result = await tool.execute(
        user_id="some-user-id",
        operation="get_memory",
    )

    assert result["success"] is False
    assert "session" in result["error"]


@pytest.mark.asyncio
async def test_tool_invalid_input(session: AsyncSession):
    """Verify tool validates input schema"""
    user = await create_user(
        session,
        email="tooltest11@example.com",
        display_name="Tool Test User 11",
        role="user",
        hashed_password=get_password_hash("testpass"),
    )

    tool = ManageUserMemoryTool()
    result = await tool.execute(
        session=session,
        user_id=user.id,
        operation="invalid_operation",
    )

    assert result["success"] is False
    assert "Invalid input" in result["error"]


@pytest.mark.asyncio
async def test_tool_get_input_schema():
    """Verify tool provides valid input schema"""
    tool = ManageUserMemoryTool()
    schema = tool.get_input_schema()

    assert "properties" in schema
    assert "operation" in schema["properties"]
    assert "content" in schema["properties"]
    assert "fact_id" in schema["properties"]
    assert "place_id" in schema["properties"]
