"""Unit tests for core utility functions"""

from __future__ import annotations

import pytest

from app.core.utils import count_tokens, count_tokens_in_dict


@pytest.mark.asyncio
async def test_count_tokens_simple_string():
    """Verify token counting for simple ASCII text"""
    text = "Hello world"
    token_count = count_tokens(text)
    assert token_count > 0
    assert token_count < len(text)


@pytest.mark.asyncio
async def test_count_tokens_empty_string():
    """Verify token counting returns 0 for empty string"""
    assert count_tokens("") == 0


@pytest.mark.asyncio
async def test_count_tokens_longer_text():
    """Verify token counting for longer text passages"""
    text = "This is a longer piece of text that should have more tokens. " * 10
    token_count = count_tokens(text)
    assert token_count > 50
    assert token_count < len(text)


@pytest.mark.asyncio
async def test_count_tokens_unicode():
    """Verify token counting handles Unicode characters"""
    text = "Hello 世界 🌍"
    token_count = count_tokens(text)
    assert token_count > 0


@pytest.mark.asyncio
async def test_count_tokens_in_dict_empty():
    """Verify token counting for empty dictionary"""
    token_count = count_tokens_in_dict({})
    assert token_count == 1


@pytest.mark.asyncio
async def test_count_tokens_in_dict_simple():
    """Verify token counting for simple dictionary"""
    data = {"name": "Alice", "age": 30}
    token_count = count_tokens_in_dict(data)
    assert token_count > 5


@pytest.mark.asyncio
async def test_count_tokens_in_dict_nested():
    """Verify token counting for nested dictionary structures"""
    data = {
        "facts": [
            {"id": "123", "content": "User prefers vegetarian food", "is_active": True},
            {"id": "456", "content": "User works in tech", "is_active": True},
        ],
        "metadata": {"total_active_facts": 2, "estimated_tokens": 100},
    }
    token_count = count_tokens_in_dict(data)
    assert token_count > 20


@pytest.mark.asyncio
async def test_count_tokens_consistency():
    """Verify count_tokens_in_dict matches count_tokens on JSON string"""
    import json

    data = {"message": "Hello world", "count": 42}
    dict_count = count_tokens_in_dict(data)
    string_count = count_tokens(json.dumps(data))
    assert dict_count == string_count
