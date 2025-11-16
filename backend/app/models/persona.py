from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Persona(Base):
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    handle: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    professional_role: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    typical_kpis: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    typical_motivations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    quintessential_queries: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
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

    user_links: Mapped[list["UserPersona"]] = relationship(
        "UserPersona", back_populates="persona", cascade="all, delete-orphan"
    )


class UserPersona(Base):
    __table_args__ = (UniqueConstraint("user_id", "persona_id", name="uq_user_persona"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    persona_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("persona.id", ondelete="CASCADE"), nullable=False, index=True
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
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

    user: Mapped["User"] = relationship("User", back_populates="persona_links")
    persona: Mapped["Persona"] = relationship("Persona", back_populates="user_links")
