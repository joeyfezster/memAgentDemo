from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.types import MessageDict, MessageRole


class ChatMessage(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str


class MessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: MessageRole
    content: str
    tool_metadata: dict | None = None
    created_at: datetime

    @classmethod
    def from_dict(
        cls, conversation_id: str, message_dict: MessageDict
    ) -> MessageSchema:
        return cls(
            conversation_id=conversation_id,
            id=message_dict.id,
            role=MessageRole(message_dict.role),
            content=message_dict.content,
            tool_metadata=message_dict.tool_metadata,
            created_at=message_dict.created_at,
        )


class ConversationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSchema]


class MessageListResponse(BaseModel):
    messages: list[MessageSchema]


class CreateConversationResponse(BaseModel):
    id: str
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class SendMessageResponse(BaseModel):
    user_message: MessageSchema
    assistant_message: MessageSchema
