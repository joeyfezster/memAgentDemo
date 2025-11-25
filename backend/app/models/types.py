from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class MessageRole(str, enum.Enum):
    USER = "user"
    SYSTEM = "system"
    AGENT = "assistant"


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
