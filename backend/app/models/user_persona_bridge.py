from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.persona import Persona
    from app.models.user import User


class UserPersonaBridge(Base):
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    persona_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("persona.id", ondelete="CASCADE"), nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    last_confirmed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    user: Mapped[User] = relationship("User", back_populates="user_personas")
    persona: Mapped[Persona] = relationship("Persona", back_populates="user_personas")
