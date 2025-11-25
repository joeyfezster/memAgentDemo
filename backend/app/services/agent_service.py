from collections.abc import AsyncIterator
import json

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.base import ToolRegistry
from app.agent.tools.placer_tools import PLACER_TOOLS
from app.core import agent_config
from app.core.config import Settings
from app.core.llm_types import AnthropicStopReason
from app.crud import conversation as conversation_crud
from app.models.types import (
    AgentResponseMetadata,
    AnthropicContentBlockType,
    AnthropicDeltaType,
    AnthropicStreamEventType,
    AnthropicToolResult,
    MessageRole,
    SSEEventType,
    ToolInteraction,
)
from app.models.user import User


class AgentService:
    """Service for AI agent operations with tool calling and streaming support."""

    def __init__(self, settings: Settings):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = agent_config.MODEL_NAME
        self.max_tokens = agent_config.MAX_TOKENS
        self.max_iterations = agent_config.MAX_ITERATIONS
        self.max_iterations_streaming = agent_config.MAX_ITERATIONS_STREAMING

        self.tool_registry = ToolRegistry()
        for tool in PLACER_TOOLS:
            self.tool_registry.register(tool)

    async def stream_response_with_tools(
        self,
        conversation_id: str,
        user_message_content: str,
        user: User,
        session: AsyncSession,
    ) -> AsyncIterator[dict]:
        """
        Stream response with ReAct tool orchestration using Claude's streaming API.

        Yields SSE events as dicts (see SSEEventType enum for event types).
        """
        conversation = await conversation_crud.get_conversation_by_id(
            session, conversation_id, user.id
        )
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = conversation.messages_document
        anthropic_messages = self._convert_to_anthropic_format(messages)
        anthropic_messages.append(
            {"role": MessageRole.USER.value, "content": user_message_content}
        )

        system_prompt = agent_config.build_system_prompt(user.display_name)
        tool_definitions = self.tool_registry.get_anthropic_schemas()

        tool_interactions: list[ToolInteraction] = []
        iteration_count = 0

        while iteration_count < self.max_iterations_streaming:
            iteration_count += 1

            async for event in self._stream_single_turn(
                anthropic_messages,
                system_prompt,
                tool_definitions,
                tool_interactions,
            ):
                yield event

                if SSEEventType.COMPLETE in event:
                    metadata = event.get("metadata", {})
                    metadata["iteration_count"] = iteration_count
                    event["metadata"] = metadata

                    if (
                        event.get("metadata", {}).get("stop_reason")
                        == AnthropicStopReason.END_TURN.value
                    ):
                        return

        metadata_obj = AgentResponseMetadata(
            tool_interactions=tool_interactions,
            iteration_count=iteration_count,
            stop_reason="max_iterations",
        )
        yield {
            SSEEventType.COMPLETE: True,
            "metadata": {
                "tool_interactions": [
                    vars(ti) for ti in metadata_obj.tool_interactions
                ],
                "iteration_count": metadata_obj.iteration_count,
                "stop_reason": metadata_obj.stop_reason,
            },
        }

    async def _stream_single_turn(
        self,
        anthropic_messages: list[dict],
        system_prompt: str,
        tool_definitions: list,
        tool_interactions: list[ToolInteraction],
    ) -> AsyncIterator[dict]:
        """
        Execute one ReAct turn with streaming.

        Yields text deltas and tool events, appends to anthropic_messages if tools called.
        """
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=anthropic_messages,
            tools=tool_definitions,
        ) as stream:
            current_tool_use = None
            current_tool_input_json = ""
            assistant_content_blocks = []
            stop_reason = None

            async for event in stream:
                if event.type == AnthropicStreamEventType.CONTENT_BLOCK_START:
                    if hasattr(event, "content_block") and hasattr(
                        event.content_block, "type"
                    ):
                        if (
                            event.content_block.type
                            == AnthropicContentBlockType.TOOL_USE
                        ):
                            current_tool_use = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                            }
                            current_tool_input_json = ""
                            assistant_content_blocks.append(
                                {
                                    "type": AnthropicContentBlockType.TOOL_USE,
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": {},
                                }
                            )
                        elif event.content_block.type == AnthropicContentBlockType.TEXT:
                            assistant_content_blocks.append(
                                {"type": AnthropicContentBlockType.TEXT, "text": ""}
                            )

                elif event.type == AnthropicStreamEventType.CONTENT_BLOCK_DELTA:
                    delta = getattr(event, "delta", None)
                    if delta:
                        if delta.type == AnthropicDeltaType.TEXT_DELTA:
                            yield {
                                SSEEventType.TEXT: delta.text,
                                "content": delta.text,
                            }
                            if (
                                assistant_content_blocks
                                and assistant_content_blocks[-1]["type"]
                                == AnthropicContentBlockType.TEXT
                            ):
                                assistant_content_blocks[-1]["text"] += delta.text
                        elif (
                            delta.type == AnthropicDeltaType.INPUT_JSON_DELTA
                            and current_tool_use
                        ):
                            current_tool_input_json += delta.partial_json

                elif (
                    event.type == AnthropicStreamEventType.CONTENT_BLOCK_STOP
                    and current_tool_use
                ):
                    try:
                        tool_input = json.loads(current_tool_input_json)
                    except json.JSONDecodeError:
                        tool_input = {}

                    for block in assistant_content_blocks:
                        if block.get("id") == current_tool_use["id"]:
                            block["input"] = tool_input
                            break

                    yield {
                        SSEEventType.TOOL_USE_START: current_tool_use["name"],
                        "tool_name": current_tool_use["name"],
                        "tool_id": current_tool_use["id"],
                        "input": tool_input,
                    }

                    tool_interactions.append(
                        ToolInteraction(
                            type=AnthropicContentBlockType.TOOL_USE,
                            id=current_tool_use["id"],
                            name=current_tool_use["name"],
                            input=tool_input,
                        )
                    )

                    current_tool_use = None
                    current_tool_input_json = ""

                elif event.type == AnthropicStreamEventType.MESSAGE_STOP:
                    stop_reason = getattr(
                        event.message, "stop_reason", AnthropicStopReason.END_TURN.value
                    )

            tool_use_blocks = [
                b
                for b in assistant_content_blocks
                if b.get("type") == AnthropicContentBlockType.TOOL_USE
            ]

            if stop_reason == AnthropicStopReason.END_TURN.value or not tool_use_blocks:
                metadata_obj = AgentResponseMetadata(
                    tool_interactions=tool_interactions,
                    iteration_count=0,
                    stop_reason=stop_reason or AnthropicStopReason.END_TURN.value,
                )
                yield {
                    SSEEventType.COMPLETE: True,
                    "metadata": {
                        "tool_interactions": [
                            vars(ti) for ti in metadata_obj.tool_interactions
                        ],
                        "iteration_count": metadata_obj.iteration_count,
                        "stop_reason": metadata_obj.stop_reason,
                    },
                }
                return

            assistant_message_for_api = []
            for block in assistant_content_blocks:
                if block["type"] == AnthropicContentBlockType.TEXT:
                    assistant_message_for_api.append(
                        {"type": AnthropicContentBlockType.TEXT, "text": block["text"]}
                    )
                elif block["type"] == AnthropicContentBlockType.TOOL_USE:
                    assistant_message_for_api.append(
                        {
                            "type": AnthropicContentBlockType.TOOL_USE,
                            "id": block["id"],
                            "name": block["name"],
                            "input": block["input"],
                        }
                    )

            anthropic_messages.append(
                {
                    "role": MessageRole.AGENT.value,
                    "content": assistant_message_for_api,
                }
            )

            tool_results = []
            for tool_use_block in tool_use_blocks:
                result, is_error = await self._execute_tool(
                    tool_use_block["id"],
                    tool_use_block["name"],
                    tool_use_block["input"],
                )

                yield {
                    SSEEventType.TOOL_RESULT: tool_use_block["name"],
                    "tool_id": tool_use_block["id"],
                    "tool_name": tool_use_block["name"],
                    "result": result,
                    "is_error": is_error,
                }

                tool_results.append(
                    {
                        "type": AnthropicContentBlockType.TOOL_RESULT,
                        "tool_use_id": tool_use_block["id"],
                        "content": json.dumps(result),
                    }
                )

                tool_interactions.append(
                    ToolInteraction(
                        type=AnthropicContentBlockType.TOOL_RESULT,
                        tool_use_id=tool_use_block["id"],
                        name=tool_use_block["name"],
                        content=result,
                        is_error=is_error,
                    )
                )

            anthropic_messages.append(
                {"role": MessageRole.USER.value, "content": tool_results}
            )

    async def _execute_tools_batch(
        self,
        tool_use_blocks: list,
        tool_interactions: list[ToolInteraction],
    ) -> list[AnthropicToolResult]:
        """
        Execute multiple tools and build Anthropic tool_result format.

        Updates tool_interactions in-place with tool_use and tool_result entries.
        Returns list of tool_result objects for Anthropic API.
        """
        tool_results: list[AnthropicToolResult] = []
        for tool_use in tool_use_blocks:
            tool_interactions.append(
                ToolInteraction(
                    type=AnthropicContentBlockType.TOOL_USE,
                    id=tool_use.id,
                    name=tool_use.name,
                    input=tool_use.input,
                )
            )

            result, is_error = await self._execute_tool(
                tool_use.id, tool_use.name, tool_use.input
            )

            content_str = (
                json.dumps(result) if isinstance(result, (dict, list)) else str(result)
            )

            tool_results.append(
                AnthropicToolResult(
                    type=AnthropicContentBlockType.TOOL_RESULT,
                    tool_use_id=tool_use.id,
                    content=content_str,
                    is_error=is_error,
                )
            )

            tool_interactions.append(
                ToolInteraction(
                    type=AnthropicContentBlockType.TOOL_RESULT,
                    tool_use_id=tool_use.id,
                    content=result,
                    is_error=is_error,
                )
            )

        return [vars(tr) for tr in tool_results]

    async def _execute_tool(
        self,
        tool_use_id: str,
        tool_name: str,
        tool_input: dict,
    ) -> tuple[dict, bool]:
        """
        Execute a single tool and return (result, is_error).

        Shared helper to eliminate duplication between streaming and non-streaming paths.
        """
        try:
            tool = self.tool_registry.get(tool_name)
            if not tool:
                raise ValueError(f"Tool {tool_name} not found")

            result = await tool.execute(**tool_input)
            is_error = isinstance(result, dict) and "error" in result
            return result, is_error

        except Exception as e:
            error_message = str(e)
            return {"error": error_message}, True

    def _extract_text_content(self, content_blocks: list) -> str:
        """Extract text from content blocks, ignoring tool_use blocks."""
        text_parts = []
        for block in content_blocks:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts) if text_parts else ""

    def _extract_tool_use_blocks(self, content_blocks: list) -> list:
        """Extract tool_use blocks from response content."""
        tool_use_blocks = []
        for block in content_blocks:
            if (
                hasattr(block, "type")
                and block.type == AnthropicContentBlockType.TOOL_USE
            ):
                if not all(hasattr(block, attr) for attr in ["id", "name", "input"]):
                    raise ValueError(
                        f"tool_use block missing required attributes: {block}"
                    )
                tool_use_blocks.append(block)
        return tool_use_blocks

    def _convert_to_anthropic_format(self, messages: list) -> list[dict[str, str]]:
        """Convert our message format to Anthropic's format."""
        anthropic_messages = []
        for msg in messages:
            role = (
                MessageRole.USER.value
                if msg["role"] == MessageRole.USER.value
                else MessageRole.AGENT.value
            )
            anthropic_messages.append({"role": role, "content": msg["content"]})
        return anthropic_messages
