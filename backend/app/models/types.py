from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, enum.Enum):
    USER = "user"
    SYSTEM = "system"
    AGENT = "assistant"


class SSEEventType(str, enum.Enum):
    """Server-Sent Event types for our streaming API (application layer)."""

    TEXT = "text"
    CHUNK = "chunk"
    TOOL_USE_START = "tool_use_start"
    TOOL_RESULT = "tool_result"
    COMPLETE = "complete"
    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"


class AnthropicContentBlockType(str, enum.Enum):
    """Content block types from Anthropic API (vendor-specific)."""

    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    TEXT = "text"


class AnthropicStreamEventType(str, enum.Enum):
    """Streaming event types from Anthropic API (vendor-specific)."""

    CONTENT_BLOCK_START = "content_block_start"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    CONTENT_BLOCK_STOP = "content_block_stop"
    MESSAGE_STOP = "message_stop"


class AnthropicDeltaType(str, enum.Enum):
    """Delta types within streaming events from Anthropic API (vendor-specific)."""

    TEXT_DELTA = "text_delta"
    INPUT_JSON_DELTA = "input_json_delta"


@dataclass
class MessageDict:
    id: str
    role: str
    content: str
    created_at: str
    tool_metadata: dict | None = None


@dataclass
class ConversationSection:
    conversation_id: int
    conversation_title: str
    conversation_created_at: datetime
    matched_message: MessageDict
    messages_before: list[MessageDict]
    messages_after: list[MessageDict]
    match_index: int
    total_messages: int


@dataclass
class ToolInteraction:
    """Record of a tool use or tool result interaction."""

    type: str
    tool_use_id: str | None = None
    id: str | None = None
    name: str | None = None
    input: dict[str, Any] | None = None
    content: Any | None = None
    is_error: bool = False


@dataclass
class AgentResponseMetadata:
    """Metadata about agent response generation."""

    tool_interactions: list[ToolInteraction]
    iteration_count: int
    stop_reason: str
    warning: str | None = None


@dataclass
class AgentResponse:
    """Complete agent response with text and metadata."""

    text: str
    metadata: AgentResponseMetadata


@dataclass
class AnthropicToolResult:
    """Tool result in Anthropic API format."""

    type: str
    tool_use_id: str
    content: str
    is_error: bool = False


POIMention = tuple[str, str]  # conversation_id, message_id
POIMentions = dict[str, list[POIMention]]


class PlacerUserDatapoint(BaseModel):
    pass


class PlacerPOI(PlacerUserDatapoint):
    place_id: str
    place_name: str
    notes: str | None = None
    mentioned_in: POIMentions = Field(default_factory=dict)
    added_at: str


class MemoryFact(BaseModel):
    id: str
    content: str = Field(min_length=1, max_length=500)
    added_at: str
    source_conversation_id: str | None = None
    source_message_id: str | None = None
    is_active: bool = True


class MemoryMetadata(BaseModel):
    last_updated: str
    total_facts: int
    total_active_facts: int
    total_pois: int
    token_count: int
    schema_version: str = "1.0"


class MemoryDocument(BaseModel):
    facts: list[MemoryFact] = Field(default_factory=list)
    placer_user_datapoints: list[PlacerPOI] = Field(default_factory=list)
    metadata: MemoryMetadata
