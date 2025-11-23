from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic
from anthropic.types import MessageStreamEvent
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import agent_config
from app.core.config import Settings
from app.crud import message as message_crud
from app.models.message import MessageRole
from app.models.user import User


class AgentService:
    def __init__(self, settings: Settings):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = agent_config.MODEL_NAME

    async def generate_response(
        self,
        conversation_id: str,
        user_message_content: str,
        user: User,
        session: AsyncSession,
    ) -> str:
        messages = await message_crud.get_conversation_messages(
            session, conversation_id
        )

        anthropic_messages = self._convert_to_anthropic_format(messages)
        anthropic_messages.append({"role": "user", "content": user_message_content})

        system_prompt = agent_config.build_system_prompt(user.display_name)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=anthropic_messages,
        )

        return response.content[0].text

    async def stream_response(
        self,
        conversation_id: str,
        user_message_content: str,
        user: User,
        session: AsyncSession,
    ) -> AsyncIterator[str]:
        messages = await message_crud.get_conversation_messages(
            session, conversation_id
        )

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
            role = "user" if msg.role == MessageRole.USER else "assistant"
            anthropic_messages.append({"role": role, "content": msg.content})
        return anthropic_messages

    def _extract_text(self, event: MessageStreamEvent) -> str:
        if event.type != "content_block_delta":
            return ""
        delta = getattr(event, "delta", None)
        if delta is None or getattr(delta, "type", "") != "text_delta":
            return ""
        return getattr(delta, "text", "")
