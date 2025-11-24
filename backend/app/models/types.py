from __future__ import annotations

import enum
from dataclasses import dataclass


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
