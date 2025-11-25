from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import count_tokens_in_dict
from app.db.base import Base
from app.models.types import (
    MemoryDocument,
    MemoryFact,
    MemoryMetadata,
    PlacerPOI,
)

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class User(Base):
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    memory_document: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        server_default=text("'{}'"),
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

    conversations: Mapped[list[Conversation]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )

    def get_memory(self) -> MemoryDocument:
        if not self.memory_document or self.memory_document == {}:
            metadata = MemoryMetadata(
                last_updated=datetime.now(UTC).isoformat(),
                total_facts=0,
                total_active_facts=0,
                total_pois=0,
                token_count=0,
                schema_version="1.0",
            )
            return MemoryDocument(
                facts=[], placer_user_datapoints=[], metadata=metadata
            )
        return MemoryDocument(**self.memory_document)

    def add_fact(
        self,
        content: str,
        source_conversation_id: str | None,
        source_message_id: str | None,
    ) -> str:
        memory = self.get_memory()
        fact_id = str(uuid4())
        new_fact = MemoryFact(
            id=fact_id,
            content=content,
            added_at=datetime.now(UTC).isoformat(),
            source_conversation_id=source_conversation_id,
            source_message_id=source_message_id,
            is_active=True,
        )
        updated_facts = [*memory.facts, new_fact]
        self.memory_document = self._build_memory_document(
            facts=updated_facts, pois=memory.placer_user_datapoints
        )
        return fact_id

    def deactivate_fact(self, fact_id: str) -> bool:
        memory = self.get_memory()
        updated_facts = []
        found = False
        for fact in memory.facts:
            if fact.id == fact_id:
                updated_fact = fact.model_copy(update={"is_active": False})
                updated_facts.append(updated_fact)
                found = True
            else:
                updated_facts.append(fact)

        if not found:
            return False

        self.memory_document = self._build_memory_document(
            facts=updated_facts, pois=memory.placer_user_datapoints
        )
        return True

    def add_poi(
        self,
        place_id: str,
        place_name: str,
        notes: str | None,
        conversation_id: str,
        message_id: str,
    ) -> str:
        memory = self.get_memory()
        new_poi = PlacerPOI(
            place_id=place_id,
            place_name=place_name,
            notes=notes,
            mentioned_in={
                conversation_id: [(message_id, datetime.now(UTC).isoformat())]
            },
            added_at=datetime.now(UTC).isoformat(),
        )
        updated_pois = [*memory.placer_user_datapoints, new_poi]
        self.memory_document = self._build_memory_document(
            facts=memory.facts, pois=updated_pois
        )
        return place_id

    def add_poi_mention(
        self, place_id: str, conversation_id: str, message_id: str
    ) -> bool:
        memory = self.get_memory()
        updated_pois = []
        found = False
        for poi in memory.placer_user_datapoints:
            if isinstance(poi, PlacerPOI) and poi.place_id == place_id:
                mentioned_in = dict(poi.mentioned_in)
                if conversation_id in mentioned_in:
                    mentioned_in[conversation_id] = [
                        *mentioned_in[conversation_id],
                        (message_id, datetime.now(UTC).isoformat()),
                    ]
                else:
                    mentioned_in[conversation_id] = [
                        (message_id, datetime.now(UTC).isoformat())
                    ]
                updated_poi = poi.model_copy(update={"mentioned_in": mentioned_in})
                updated_pois.append(updated_poi)
                found = True
            else:
                updated_pois.append(poi)

        if not found:
            return False

        self.memory_document = self._build_memory_document(
            facts=memory.facts, pois=updated_pois
        )
        return True

    def get_active_facts(self) -> list[MemoryFact]:
        memory = self.get_memory()
        return [fact for fact in memory.facts if fact.is_active]

    def _calculate_metadata(
        self,
        facts: list[MemoryFact],
        pois: list[PlacerPOI],
    ) -> MemoryMetadata:
        doc_dict = {
            "facts": [f.model_dump() for f in facts],
            "placer_user_datapoints": [p.model_dump() for p in pois],
        }
        token_count = count_tokens_in_dict(doc_dict)
        total_active = sum(1 for f in facts if f.is_active)

        return MemoryMetadata(
            last_updated=datetime.now(UTC).isoformat(),
            total_facts=len(facts),
            total_active_facts=total_active,
            total_pois=len(pois),
            token_count=token_count,
            schema_version="1.0",
        )

    def _build_memory_document(
        self, facts: list[MemoryFact], pois: list[PlacerPOI]
    ) -> dict:
        """Standardized method to create memory_document dict to prevent key name errors"""
        return {
            "facts": [f.model_dump() for f in facts],
            "placer_user_datapoints": [p.model_dump() for p in pois],
            "metadata": self._calculate_metadata(facts, pois).model_dump(),
        }
