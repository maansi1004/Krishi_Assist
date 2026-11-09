from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def my_audit_trail(limit: int = Query(50, ge=1, le=200), user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The signed-in farmer's own recent activity, newest first."""
    rows = db.query(AuditLog).filter_by(user_id=user.id).order_by(AuditLog.id.desc()).limit(limit).all()
    return [{"id": r.id, "event": r.event_type, "payload": r.payload, "createdAt": r.created_at} for r in rows]
