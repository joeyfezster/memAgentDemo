"""Memory model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func

from app.db.base import Base


class Memory(Base):
    """Memory model for storing agent memories."""

    __tablename__ = "memories"

    id = Column(String, primary_key=True, index=True)
    content = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
