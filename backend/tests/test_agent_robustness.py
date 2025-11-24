"""
Tests for agent robustness: error handling, stop_reason validation, API contract assumptions.

These tests verify that the agent service gracefully handles:
1. Tools that return errors (never throw exceptions)
2. Unexpected stop_reason values from LLM
3. Malformed response.content structures
4. Async tool execution failures
5. Edge cases in response parsing
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

from app.agent.tools.base import ToolRegistry
from app.agent.tools.placer_tools import SearchPlacesTool
from app.core.config import Settings
from app.core.llm_types import AnthropicStopReason
from app.services.agent_service import AgentService


async def async_return(result):
    return result


@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.anthropic_api_key = "test-key"
    return settings


@pytest.fixture
def agent_service(mock_settings):
    return AgentService(mock_settings)


class TestToolErrorHandling:
    """Test that tools never throw exceptions - always return error dicts"""

    @pytest.mark.asyncio
    async def test_tool_invalid_input_returns_error_dict(self):
        """Tools should catch Pydantic validation errors and return error dict"""
        tool = SearchPlacesTool()

        # Missing required field
        result = await tool.execute(query="test")  # missing state

        assert "error" in result
        assert "Invalid input parameters" in result["error"]
        assert result["total"] == 0
        assert result["places"] == []

    @pytest.mark.asyncio
    async def test_tool_wrong_type_returns_error_dict(self):
        """Tools should handle type mismatches gracefully"""
        tool = SearchPlacesTool()

        # Wrong type for max_results
        result = await tool.execute(
            query="test", state="CA", max_results="not-a-number"
        )

        assert "error" in result


class TestStopReasonHandling:
    """Test validation and handling of LLM stop_reason values"""

    @pytest.mark.asyncio
    async def test_unknown_stop_reason_raises_error(self, agent_service):
        """Unknown stop_reason should raise ValueError"""
        mock_response = MagicMock(spec=Message)
        mock_response.stop_reason = "unknown_reason"
        mock_response.content = []
        mock_response.usage = Usage(input_tokens=10, output_tokens=10)

        mock_conversation = MagicMock()
        mock_conversation.messages_document = []

        with patch.object(
            agent_service.client.messages,
            "create",
            return_value=async_return(mock_response),
        ):
            with patch.object(
                agent_service, "_convert_to_anthropic_format", return_value=[]
            ):
                with patch(
                    "app.services.agent_service.conversation_crud.get_conversation_by_id",
                    new_callable=AsyncMock,
                    return_value=mock_conversation,
                ):
                    mock_session = AsyncMock()
                    mock_user = MagicMock()

                    with pytest.raises(ValueError, match="Unexpected stop_reason"):
                        await agent_service.generate_response_with_tools(
                            "conv-123", "test query", mock_user, mock_session
                        )

    @pytest.mark.asyncio
    async def test_all_valid_stop_reasons_accepted(self, agent_service):
        """All AnthropicStopReason enum values should be accepted"""
        from app.core.llm_types import is_stop_reason_legal

        for reason in AnthropicStopReason:
            assert is_stop_reason_legal(reason.value) is True

        assert is_stop_reason_legal("invalid") is False
        assert is_stop_reason_legal(None) is False


class TestResponseContentParsing:
    """Test parsing of response.content structure"""

    @pytest.mark.asyncio
    async def test_tool_use_without_blocks_raises_error(self, agent_service):
        """stop_reason=tool_use but no tool_use blocks should raise ValueError"""
        mock_response = MagicMock(spec=Message)
        mock_response.stop_reason = AnthropicStopReason.TOOL_USE.value
        mock_response.content = []  # No blocks!
        mock_response.usage = Usage(input_tokens=10, output_tokens=10)

        mock_conversation = MagicMock()
        mock_conversation.messages_document = []

        with patch.object(
            agent_service.client.messages,
            "create",
            return_value=async_return(mock_response),
        ):
            with patch.object(
                agent_service, "_convert_to_anthropic_format", return_value=[]
            ):
                with patch(
                    "app.services.agent_service.conversation_crud.get_conversation_by_id",
                    new_callable=AsyncMock,
                    return_value=mock_conversation,
                ):
                    mock_session = AsyncMock()
                    mock_user = MagicMock()

                    with pytest.raises(ValueError, match="no tool_use blocks"):
                        await agent_service.generate_response_with_tools(
                            "conv-123", "test query", mock_user, mock_session
                        )

    @pytest.mark.asyncio
    async def test_malformed_tool_use_block_raises_error(self, agent_service):
        """tool_use block missing required attributes should raise ValueError"""
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_places"
        # Ensure attributes are missing for hasattr check
        del mock_tool_block.id
        del mock_tool_block.input

        mock_response = MagicMock(spec=Message)
        mock_response.stop_reason = AnthropicStopReason.TOOL_USE.value
        mock_response.content = [mock_tool_block]
        mock_response.usage = Usage(input_tokens=10, output_tokens=10)

        mock_conversation = MagicMock()
        mock_conversation.messages_document = []

        with patch.object(
            agent_service.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with patch.object(
                agent_service, "_convert_to_anthropic_format", return_value=[]
            ):
                with patch(
                    "app.services.agent_service.conversation_crud.get_conversation_by_id",
                    new_callable=AsyncMock,
                    return_value=mock_conversation,
                ):
                    mock_session = AsyncMock()
                    mock_user = MagicMock()

                    with pytest.raises(ValueError, match="missing required attributes"):
                        await agent_service.generate_response_with_tools(
                            "conv-123", "test query", mock_user, mock_session
                        )

    def test_extract_text_content_handles_empty(self, agent_service):
        """_extract_text_content should handle empty content"""
        assert agent_service._extract_text_content([]) == ""

    def test_extract_tool_use_blocks_validates_structure(self, agent_service):
        """_extract_tool_use_blocks should validate block structure"""
        valid_block = MagicMock()
        valid_block.type = "tool_use"
        valid_block.id = "tool-123"
        valid_block.name = "search_places"
        valid_block.input = {"query": "test"}

        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Some text"

        content = [text_block, valid_block]
        result = agent_service._extract_tool_use_blocks(content)

        assert len(result) == 1
        assert result[0].name == "search_places"


class TestToolRegistryErrorHandling:
    """Test that ToolRegistry handles tool execution errors"""

    @pytest.mark.asyncio
    async def test_registry_executes_tool_safely(self):
        """Registry should call tool.execute() and return result or error"""
        registry = ToolRegistry()
        tool = SearchPlacesTool()
        registry.register(tool)

        # Valid execution
        result = await registry.execute("search_places", query="coffee", state="CA")
        assert "places" in result

        # Invalid execution - tool returns error dict
        result = await registry.execute("search_places", query="test")  # missing state
        assert "error" in result

    @pytest.mark.asyncio
    async def test_registry_unknown_tool_raises(self):
        """Registry should raise ValueError for unknown tools"""
        registry = ToolRegistry()

        with pytest.raises(ValueError, match="not found in registry"):
            await registry.execute("unknown_tool", param="value")


class TestEndToEndRobustness:
    """Integration tests for full ReAct loop robustness"""

    @pytest.mark.asyncio
    async def test_tool_error_continues_loop(self, agent_service):
        """Tool returning error dict should not crash loop"""
        # First response: tool_use with invalid params
        mock_tool_block = MagicMock(spec=ToolUseBlock)
        mock_tool_block.type = "tool_use"
        mock_tool_block.id = "tool-123"
        mock_tool_block.name = "search_places"
        mock_tool_block.input = {"query": "test"}  # Missing state - will error

        first_response = MagicMock(spec=Message)
        first_response.stop_reason = AnthropicStopReason.TOOL_USE.value
        first_response.content = [mock_tool_block]
        first_response.usage = Usage(input_tokens=10, output_tokens=10)

        # Second response: end_turn with recovery message
        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.type = "text"
        mock_text_block.text = "I encountered an error. Let me try again."

        second_response = MagicMock(spec=Message)
        second_response.stop_reason = AnthropicStopReason.END_TURN.value
        second_response.content = [mock_text_block]
        second_response.usage = Usage(input_tokens=10, output_tokens=20)

        mock_conversation = MagicMock()
        mock_conversation.messages_document = []

        with patch.object(
            agent_service.client.messages,
            "create",
            side_effect=[async_return(first_response), async_return(second_response)],
        ):
            with patch.object(
                agent_service, "_convert_to_anthropic_format", return_value=[]
            ):
                with patch(
                    "app.services.agent_service.conversation_crud.get_conversation_by_id",
                    new_callable=AsyncMock,
                    return_value=mock_conversation,
                ):
                    mock_session = AsyncMock()
                    mock_user = MagicMock()

                    text, metadata = await agent_service.generate_response_with_tools(
                        "conv-123", "test query", mock_user, mock_session
                    )

                    # Should complete successfully despite tool error
                    assert "error" in text.lower() or "try again" in text.lower()
                    assert metadata["iteration_count"] == 2
                    assert (
                        len(metadata["tool_interactions"]) == 2
                    )  # tool_use + tool_result

                    # Verify tool_result has error
                    tool_result = metadata["tool_interactions"][1]
                    assert tool_result["type"] == "tool_result"
                    assert tool_result["is_error"] is True
