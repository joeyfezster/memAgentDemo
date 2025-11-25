"""Unit tests for agent configuration and system prompt building"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.agent_config import build_system_prompt
from app.models.types import MemoryDocument, MemoryFact, MemoryMetadata, PlacerPOI


@pytest.mark.asyncio
async def test_system_prompt_includes_datetime():
    """Verify system prompt includes current datetime in ISO format"""
    system_prompt = build_system_prompt("Test User")

    assert "Current datetime:" in system_prompt

    current_year = datetime.now(UTC).year
    assert str(current_year) in system_prompt

    assert system_prompt.count("T") >= 1
    assert system_prompt.count("Z") >= 1 or system_prompt.count("+") >= 1


@pytest.mark.asyncio
async def test_system_prompt_includes_user_memory():
    """Verify system prompt includes user memory when provided"""
    from app.core.agent_config import format_user_memory

    memory = MemoryDocument(
        facts=[
            MemoryFact(
                id="fact-1",
                content="Prefers vegetarian food",
                added_at="2025-11-20T14:30:00+00:00",
                source_conversation_id="conv-1",
                source_message_id="msg-1",
                is_active=True,
            ),
            MemoryFact(
                id="fact-2",
                content="Works as a software engineer",
                added_at="2025-11-21T09:15:00+00:00",
                source_conversation_id="conv-1",
                source_message_id="msg-2",
                is_active=True,
            ),
        ],
        placer_user_datapoints=[
            PlacerPOI(
                place_id="ChIJseam3sK0j4ARSMSb-oaUO6o",
                place_name="Microsoft Redmond Campus",
                notes="User's workplace",
                mentioned_in={"conv-1": [("msg-3", "2025-11-21T10:00:00+00:00")]},
                added_at="2025-11-21T10:00:00+00:00",
            )
        ],
        metadata=MemoryMetadata(
            last_updated="2025-11-21T10:00:00+00:00",
            total_facts=2,
            total_active_facts=2,
            total_pois=1,
            token_count=150,
            schema_version="1.0",
        ),
    )

    user_memory_text = format_user_memory(memory)
    system_prompt = build_system_prompt("Test User", user_memory=user_memory_text)

    assert "USER'S STORED MEMORIES:" in system_prompt
    assert "vegetarian" in system_prompt
    assert "software engineer" in system_prompt
    assert "PLACES OF INTEREST:" in system_prompt
    assert "Microsoft Redmond Campus" in system_prompt


@pytest.mark.asyncio
async def test_system_prompt_without_user_memory():
    """Verify system prompt works correctly without user memory"""
    system_prompt = build_system_prompt("Test User", user_memory=None)

    assert "Test User" in system_prompt
    assert "What I Know About You" not in system_prompt

    system_prompt_empty = build_system_prompt("Test User", user_memory="")
    assert "What I Know About You" not in system_prompt_empty


@pytest.mark.asyncio
async def test_format_user_memory():
    """Verify format_user_memory creates well-formatted markdown"""
    from app.core.agent_config import format_user_memory

    memory = MemoryDocument(
        facts=[
            MemoryFact(
                id="fact-1",
                content="User prefers vegetarian food",
                added_at="2025-11-25T10:00:00+00:00",
                source_conversation_id="conv-1",
                source_message_id="msg-1",
                is_active=True,
            ),
            MemoryFact(
                id="fact-2",
                content="User works as a software engineer",
                added_at="2025-11-25T10:05:00+00:00",
                source_conversation_id="conv-1",
                source_message_id="msg-2",
                is_active=True,
            ),
        ],
        placer_user_datapoints=[
            PlacerPOI(
                place_id="poi-1",
                place_name="Microsoft Redmond Campus",
                notes="User's workplace",
                mentioned_in={"conv-1": [("msg-3", "2025-11-25T10:10:00+00:00")]},
                added_at="2025-11-25T10:10:00+00:00",
            )
        ],
        metadata=MemoryMetadata(
            last_updated="2025-11-25T10:10:00+00:00",
            total_facts=2,
            total_active_facts=2,
            total_pois=1,
            token_count=100,
            schema_version="1.0",
        ),
    )

    formatted = format_user_memory(memory)

    assert "USER'S STORED MEMORIES:" in formatted
    assert "vegetarian food" in formatted
    assert "software engineer" in formatted
    assert "PLACES OF INTEREST:" in formatted
    assert "Microsoft Redmond Campus" in formatted
    assert "workplace" in formatted
