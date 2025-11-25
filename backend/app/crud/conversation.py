from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.types import MessageDict


async def create_conversation(session: AsyncSession, *, user_id: str) -> Conversation:
    conversation = Conversation(user_id=user_id, messages_document=[])
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def get_user_conversations(
    session: AsyncSession, user_id: str
) -> list[Conversation]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation_by_id(
    session: AsyncSession, conversation_id: str, user_id: str
) -> Conversation | None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def update_conversation_title(
    session: AsyncSession, conversation_id: str, title: str
) -> None:
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        conversation.title = title
        await session.commit()


async def add_message_to_conversation(
    session: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    tool_metadata: dict | None = None,
) -> MessageDict:
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise ValueError(f"Conversation {conversation_id} not found")

    message = conversation.add_message(role, content, tool_metadata)
    await session.commit()
    await session.refresh(conversation)
    return message


async def get_conversation_messages(
    session: AsyncSession, conversation_id: str
) -> list[MessageDict]:
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return []
    return conversation.get_messages()


async def get_message_count(session: AsyncSession, conversation_id: str) -> int:
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return 0
    return conversation.get_message_count()
