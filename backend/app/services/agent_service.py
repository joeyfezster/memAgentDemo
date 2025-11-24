from collections.abc import AsyncIterator
import json

from anthropic import AsyncAnthropic
from anthropic.types import MessageStreamEvent
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.base import ToolRegistry
from app.agent.tools.placer_tools import PLACER_TOOLS
from app.core import agent_config
from app.core.config import Settings
from app.core.llm_types import AnthropicStopReason, is_stop_reason_legal
from app.crud import conversation as conversation_crud
from app.models.types import MessageRole
from app.models.user import User


class AgentService:
    def __init__(self, settings: Settings):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = agent_config.MODEL_NAME
        self.max_iterations = 10

        self.tool_registry = ToolRegistry()
        for tool in PLACER_TOOLS:
            self.tool_registry.register(tool)

    async def generate_response(
        self,
        conversation_id: str,
        user_message_content: str,
        user: User,
        session: AsyncSession,
    ) -> str:
        """
        Legacy method for backward compatibility.
        Calls generate_response_with_tools and returns only the text.
        """
        text, _metadata = await self.generate_response_with_tools(
            conversation_id, user_message_content, user, session
        )
        return text

    async def generate_response_with_tools(
        self,
        conversation_id: str,
        user_message_content: str,
        user: User,
        session: AsyncSession,
    ) -> tuple[str, dict]:
        """
        Generate response using ReAct loop with tool calling.

        This implements server-side tool orchestration:
        1. Call Anthropic with tool definitions
        2. Anthropic responds with tool_use requests
        3. WE execute tools in our backend
        4. Feed results back to Anthropic
        5. Repeat until final text response

        Returns:
            tuple: (final_text_response, metadata_dict)
        """
        conversation = await conversation_crud.get_conversation_by_id(
            session, conversation_id, user.id
        )
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = conversation.messages_document

        agent_ReAct_messages = self._convert_to_anthropic_format(messages)
        agent_ReAct_messages.append({"role": "user", "content": user_message_content})

        system_prompt = agent_config.build_system_prompt(user.display_name)
        tool_schemas = self.tool_registry.get_anthropic_schemas()

        tool_interactions = []
        iteration_count = 0

        while iteration_count < self.max_iterations:
            iteration_count += 1

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=agent_ReAct_messages,
                tools=tool_schemas,
            )

            if not is_stop_reason_legal(response.stop_reason):
                raise ValueError(
                    f"Unexpected stop_reason from LLM: {response.stop_reason}. "
                    f"Expected one of: {[r.value for r in AnthropicStopReason]}"
                )

            if response.stop_reason == AnthropicStopReason.END_TURN.value:
                final_text = self._extract_text_content(response.content)

                return final_text, {
                    "tool_interactions": tool_interactions,
                    "iteration_count": iteration_count,
                    "stop_reason": response.stop_reason,
                }

            elif response.stop_reason == AnthropicStopReason.MAX_TOKENS.value:
                final_text = self._extract_text_content(response.content)
                return final_text, {
                    "tool_interactions": tool_interactions,
                    "iteration_count": iteration_count,
                    "stop_reason": response.stop_reason,
                    "warning": "Response truncated due to max_tokens limit",
                }

            elif response.stop_reason == AnthropicStopReason.TOOL_USE.value:
                tool_use_blocks = self._extract_tool_use_blocks(response.content)

                if not tool_use_blocks:
                    raise ValueError(
                        f"stop_reason=tool_use but no tool_use blocks in content: {response.content}"
                    )

                agent_ReAct_messages.append(
                    {"role": "assistant", "content": response.content}
                )

                # 4. Execute tools SERVER-SIDE (sequential for MVP)
                tool_results = []
                for tool_use in tool_use_blocks:
                    tool_interactions.append(
                        {
                            "type": "tool_use",
                            "id": tool_use.id,
                            "name": tool_use.name,
                            "input": tool_use.input,
                        }
                    )

                    try:
                        result = await self.tool_registry.execute(
                            tool_use.name, **tool_use.input
                        )

                        is_error = isinstance(result, dict) and "error" in result

                        content_str = (
                            json.dumps(result)
                            if isinstance(result, (dict, list))
                            else str(result)
                        )

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": content_str,
                                "is_error": is_error,
                            }
                        )

                        tool_interactions.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": result,  # Keep original object for metadata/logging
                                "is_error": is_error,
                            }
                        )

                    except Exception as e:
                        error_msg = f"Error executing {tool_use.name}: {str(e)}"
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": error_msg,
                                "is_error": True,
                            }
                        )

                        tool_interactions.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": error_msg,
                                "is_error": True,
                            }
                        )

                agent_ReAct_messages.append({"role": "user", "content": tool_results})

                continue

            else:
                raise ValueError(f"Unhandled stop_reason: {response.stop_reason}")

        return (
            "I apologize, but I've reached my processing limit. Please try rephrasing your question.",
            {
                "tool_interactions": tool_interactions,
                "iteration_count": iteration_count,
                "stop_reason": "max_iterations",
            },
        )

    def _extract_text_content(self, content_blocks: list) -> str:
        """
        Extract text from content blocks, ignoring tool_use blocks.

        Safely handles various content block types from Anthropic API.
        """
        text_parts = []
        for block in content_blocks:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts) if text_parts else ""

    def _extract_tool_use_blocks(self, content_blocks: list) -> list:
        """
        Extract tool_use blocks from response content.

        Validates that blocks have expected structure (type, id, name, input).
        Raises ValueError if block structure is invalid.
        """
        tool_use_blocks = []
        for block in content_blocks:
            if hasattr(block, "type") and block.type == "tool_use":
                if not all(hasattr(block, attr) for attr in ["id", "name", "input"]):
                    raise ValueError(
                        f"tool_use block missing required attributes: {block}"
                    )
                tool_use_blocks.append(block)
        return tool_use_blocks

    async def stream_response(
        self,
        conversation_id: str,
        user_message_content: str,
        user: User,
        session: AsyncSession,
    ) -> AsyncIterator[str]:
        conversation = await conversation_crud.get_conversation_by_id(
            session, conversation_id, user.id
        )
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = conversation.messages_document

        anthropic_messages = self._convert_to_anthropic_format(messages)
        anthropic_messages.append({"role": "user", "content": user_message_content})

        system_prompt = agent_config.build_system_prompt(user.display_name)

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=anthropic_messages,
        ) as stream:
            async for event in stream:
                text_chunk = self._extract_text(event)
                if text_chunk:
                    yield text_chunk

    def _convert_to_anthropic_format(self, messages: list) -> list[dict[str, str]]:
        anthropic_messages = []
        for msg in messages:
            role = "user" if msg["role"] == MessageRole.USER.value else "assistant"
            anthropic_messages.append({"role": role, "content": msg["content"]})
        return anthropic_messages

    def _extract_text(self, event: MessageStreamEvent) -> str:
        if event.type != "content_block_delta":
            return ""
        delta = getattr(event, "delta", None)
        if delta is None or getattr(delta, "type", "") != "text_delta":
            return ""
        return getattr(delta, "text", "")
