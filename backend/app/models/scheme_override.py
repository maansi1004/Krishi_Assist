from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SchemeOverride(Base):
    """An administrator's decision about one scheme, laid on top of schemes.json.

    The JSON file is never rewritten at runtime. Anything set here (switched off, marked
    verified on a date) wins over the file, and deleting the row restores the file's values.
    """
    __tablename__ = "scheme_overrides"
    scheme_code: Mapped[str] = mapped_column(String(80), primary_key=True)
    status: Mapped[str] = mapped_column(String(30))
    last_verified_at: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
