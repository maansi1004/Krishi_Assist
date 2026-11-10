from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Document(Base):
    """One uploaded file. The file itself lives on disk; only facts about it are stored here.

    stored_name is random and made by the server. The name the farmer gave the file is kept
    only to show it back to them and is never used to build a path.
    """
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("user_id", "sha256", name="uq_document_user_sha"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String(40))
    original_name: Mapped[str] = mapped_column(String(120))
    stored_name: Mapped[str] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(60))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DocumentChoice(Base):
    """What a farmer said about ONE document that ONE scheme asks for, when no file is uploaded for it:
    "I have it" (no upload needed), "I don't have it yet" (show how to get it) or "not applicable to me".
    """
    __tablename__ = "document_choices"
    __table_args__ = (UniqueConstraint("user_id", "scheme_code", "document_name", name="uq_document_choice"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    scheme_code: Mapped[str] = mapped_column(String(80), index=True)
    document_name: Mapped[str] = mapped_column(String(200))
    choice: Mapped[str] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
