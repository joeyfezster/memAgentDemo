from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.crud import conversation as conversation_crud
from app.db.session import get_session
from app.models.types import MessageRole, SSEEventType
from app.models.user import User
from app.schemas.chat import (
    ChatMessage,
    ChatResponse,
    ConversationListResponse,
    ConversationSchema,
    CreateConversationResponse,
    MessageListResponse,
    MessageSchema,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
async def create_message(
    payload: ChatMessage, current_user: User = Depends(get_current_user)
) -> ChatResponse:
    reply_text = f"hi {current_user.display_name}"
    return ChatResponse(reply=reply_text)


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CreateConversationResponse:
    conversation = await conversation_crud.create_conversation(
        session, user_id=current_user.id
    )
    return CreateConversationResponse(
        id=conversation.id, created_at=conversation.created_at
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationListResponse:
    conversations = await conversation_crud.get_user_conversations(
        session, current_user.id
    )
    return ConversationListResponse(
        conversations=[
            ConversationSchema.model_validate(conv) for conv in conversations
        ]
    )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=MessageListResponse
)
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageListResponse:
    conversation = await conversation_crud.get_conversation_by_id(
        session, conversation_id, current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    message_dicts = await conversation_crud.get_conversation_messages(
        session, conversation_id
    )
    messages = [MessageSchema.from_dict(conversation_id, msg) for msg in message_dicts]
    return MessageListResponse(messages=messages)


@router.post(
    "/conversations/{conversation_id}/messages", response_model=SendMessageResponse
)
async def send_message_to_conversation(
    conversation_id: str,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SendMessageResponse:
    conversation = await conversation_crud.get_conversation_by_id(
        session, conversation_id, current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    user_message_dict = await conversation_crud.add_message_to_conversation(
        session,
        conversation_id=conversation_id,
        role=MessageRole.USER.value,
        content=payload.content,
        tool_metadata=None,
    )

    settings = get_settings()
    agent_service = AgentService(settings)
    agent_response = await agent_service.stream_response_with_tools(
        conversation_id=conversation_id,
        user_message_content=payload.content,
        user=current_user,
        session=session,
        user_message_id=user_message_dict.id,
    )

    metadata_dict = {
        "tool_interactions": [
            vars(ti) for ti in agent_response.metadata.tool_interactions
        ],
        "iteration_count": agent_response.metadata.iteration_count,
        "stop_reason": agent_response.metadata.stop_reason,
    }
    if agent_response.metadata.warning:
        metadata_dict["warning"] = agent_response.metadata.warning

    assistant_message_dict = await conversation_crud.add_message_to_conversation(
        session,
        conversation_id=conversation_id,
        role=MessageRole.AGENT.value,
        content=agent_response.text,
        tool_metadata=metadata_dict,
    )

    await _ensure_conversation_title(
        session, conversation_id, current_user.id, payload.content
    )

    user_message = MessageSchema.from_dict(conversation_id, user_message_dict)
    assistant_message = MessageSchema.from_dict(conversation_id, assistant_message_dict)

    return SendMessageResponse(
        user_message=user_message, assistant_message=assistant_message
    )


@router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message_to_conversation(
    conversation_id: str,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    conversation = await conversation_crud.get_conversation_by_id(
        session, conversation_id, current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    user_message_dict = await conversation_crud.add_message_to_conversation(
        session,
        conversation_id=conversation_id,
        role=MessageRole.USER.value,
        content=payload.content,
    )
    user_message = MessageSchema.from_dict(conversation_id, user_message_dict)

    settings = get_settings()
    agent_service = AgentService(settings)

    async def event_stream() -> AsyncIterator[str]:
        yield _format_sse(
            {
                "type": SSEEventType.USER_MESSAGE,
                "message": _serialize_message(user_message),
            }
        )

        assistant_text_parts = []
        assistant_metadata = None

        async for event in agent_service.stream_response_with_tools(
            conversation_id=conversation_id,
            user_message_content=payload.content,
            user=current_user,
            session=session,
            user_message_id=user_message_dict.id,
        ):
            print(f"[STREAM EVENT] {event}")
            if SSEEventType.TEXT in event:
                assistant_text_parts.append(event["content"])
                yield _format_sse(
                    {"type": SSEEventType.CHUNK, "content": event["content"]}
                )
            elif SSEEventType.TOOL_USE_START in event:
                print(f"[TOOL USE START] Sending: {event}")
                yield _format_sse(
                    {
                        "type": SSEEventType.TOOL_USE_START,
                        **{
                            k: v
                            for k, v in event.items()
                            if k != SSEEventType.TOOL_USE_START
                        },
                    }
                )
            elif SSEEventType.TOOL_RESULT in event:
                print(f"[TOOL RESULT] Sending: {event}")
                yield _format_sse(
                    {
                        "type": SSEEventType.TOOL_RESULT,
                        **{
                            k: v
                            for k, v in event.items()
                            if k != SSEEventType.TOOL_RESULT
                        },
                    }
                )
            elif SSEEventType.COMPLETE in event:
                assistant_metadata = event["metadata"]

        assistant_reply = "".join(assistant_text_parts) if assistant_text_parts else ""

        assistant_message_dict = await conversation_crud.add_message_to_conversation(
            session,
            conversation_id=conversation_id,
            role=MessageRole.AGENT.value,
            content=assistant_reply,
            tool_metadata=assistant_metadata,
        )
        assistant_message = MessageSchema.from_dict(
            conversation_id, assistant_message_dict
        )

        await _ensure_conversation_title(
            session, conversation_id, current_user.id, payload.content
        )

        print(f"[FINAL MESSAGE] assistant_message: {assistant_message}")
        print(f"[FINAL MESSAGE] tool_metadata: {assistant_metadata}")

        yield _format_sse(
            {
                "type": SSEEventType.ASSISTANT_MESSAGE,
                "message": _serialize_message(assistant_message),
            }
        )
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


async def _ensure_conversation_title(
    session: AsyncSession, conversation_id: str, user_id: str, user_content: str
) -> None:
    conversation = await conversation_crud.get_conversation_by_id(
        session, conversation_id, user_id
    )
    if not conversation:
        return

    message_count = await conversation_crud.get_message_count(session, conversation_id)
    if message_count < 2 or conversation.title:
        return

    words = user_content.split()[:4]
    title_prefix = " ".join(words)
    timestamp = datetime.now().strftime("%d-%m:%H:%M")
    title = f"{title_prefix} {timestamp}"
    await conversation_crud.update_conversation_title(session, conversation_id, title)


def _serialize_message(message: MessageSchema) -> dict[str, Any]:
    return message.model_dump(mode="json")


def _format_sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"
