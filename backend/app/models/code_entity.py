from uuid import uuid4

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodeEntity(Base):
    __tablename__ = "code_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("code_files.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_entity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("code_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # FILE, MODULE, FUNCTION, CLASS, METHOD
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    qualified_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_code_entities_repo_type", "repository_id", "entity_type"),
    )
