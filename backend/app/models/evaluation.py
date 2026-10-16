from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scheme_code: Mapped[str] = mapped_column(String(80), index=True)
    scheme_version: Mapped[str|None] = mapped_column(String(80))
    rule_version: Mapped[str] = mapped_column(String(30), default="1")
    overall_result: Mapped[str] = mapped_column(String(40))
    profile_snapshot: Mapped[dict] = mapped_column(JSON)
    criterion_results: Mapped[list] = mapped_column(JSON, default=list)
    missing_fields: Mapped[list] = mapped_column(JSON, default=list)
    remediation_steps: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
