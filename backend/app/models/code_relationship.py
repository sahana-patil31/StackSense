from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodeRelationship(Base):
    __tablename__ = "code_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    source_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("code_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    target_entity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("code_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CONTAINS, IMPORTS, CALLS, DEFINES
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_target: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index("ix_code_relationships_repo_type", "repository_id", "relationship_type"),
    )
