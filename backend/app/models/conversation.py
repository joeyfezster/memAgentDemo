from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import get_settings
from app.db.base import Base
from app.models.types import MessageDict

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(Base):
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    messages_document: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        server_default=text("'[]'"),
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(get_settings().embedding_dimension), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    user: Mapped[User] = relationship("User", back_populates="conversations")

    def add_message(
        self, role: str, content: str, tool_metadata: dict | None = None
    ) -> MessageDict:
        message_dict = {
            "id": str(uuid4()),
            "role": role,
            "content": content,
            "created_at": datetime.now(UTC).isoformat(),
            "tool_metadata": tool_metadata,
        }
        if self.messages_document is None:
            self.messages_document = []
        self.messages_document = [*self.messages_document, message_dict]
        return MessageDict(**message_dict)

    def get_messages(self) -> list[MessageDict]:
        return [MessageDict(**msg) for msg in (self.messages_document or [])]

    def get_message_count(self) -> int:
        return len(self.messages_document) if self.messages_document else 0
