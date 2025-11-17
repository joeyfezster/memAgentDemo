from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user_persona_bridge import UserPersonaBridge


class Persona(Base):
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    persona_handle: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    persona_character_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    professional_role: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    typical_kpis: Mapped[str] = mapped_column(Text, nullable=False)
    typical_motivations: Mapped[str] = mapped_column(Text, nullable=False)
    quintessential_queries: Mapped[str] = mapped_column(Text, nullable=False)
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

    user_personas: Mapped[list[UserPersonaBridge]] = relationship(
        "UserPersonaBridge", back_populates="persona", cascade="all, delete-orphan"
    )
