from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.message import MessageRole


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
    created_at: datetime


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
    tool_calls: list["ToolCallSchema"] = Field(default_factory=list)


class ToolCallSchema(BaseModel):
    name: str
    arguments: dict | None = None
