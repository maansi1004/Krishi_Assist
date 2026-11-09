from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.scheme_override import SchemeOverride
from app.models.user import User
from app.services.audit import log_event
from app.services.scheme_admin import (coverage_report, criteria_count, list_scheme_rows, refresh_overrides,
                                       scheme_row, validate_scheme_dict)
from app.services.scheme_service import get_scheme_any, load_file_schemes

router = APIRouter(prefix="/api/admin", tags=["admin"])

SchemeStatus = Literal["active", "verification_required", "inactive"]


class SchemeUpdate(BaseModel):
    status: SchemeStatus
    # The date the scheme data was last checked against the official source. Defaults to today.
    last_verified_at: date | None = None
    note: str | None = Field(default=None, max_length=500)
    # Needed to switch on a scheme that has only one eligibility rule.
    acknowledge_single_rule: bool = False


class ValidateRequest(BaseModel):
    scheme: dict


def _file_scheme(code: str) -> dict | None:
    return next((s for s in load_file_schemes() if s["schemeCode"] == code), None)


@router.get("/schemes")
def list_schemes(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return list_scheme_rows(db)


@router.put("/schemes/{scheme_code}")
def update_scheme(scheme_code: str, body: SchemeUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    scheme = get_scheme_any(scheme_code)
    if not scheme:
        raise HTTPException(404, "Scheme not found")
    verified = body.last_verified_at
    if body.status == "active":
        verified = verified or datetime.now(timezone.utc).date()
        if not scheme.get("sources"):
            raise HTTPException(422, "A scheme needs at least one source before it can be switched on.")
        if criteria_count(scheme) <= 1 and not body.acknowledge_single_rule:
            raise HTTPException(409, "This scheme has only one eligibility rule. Check the official guideline has no other conditions, then confirm with acknowledge_single_rule=true.")
    if verified and verified > datetime.now(timezone.utc).date():
        raise HTTPException(422, "The verification date cannot be in the future.")

    before = scheme.get("status")
    row = db.get(SchemeOverride, scheme_code) or SchemeOverride(scheme_code=scheme_code)
    row.status = body.status
    row.last_verified_at = verified.isoformat() if verified else None
    row.note = body.note
    row.updated_by = admin.id
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    db.commit()
    refresh_overrides(db)
    log_event(db, admin.id, "admin_scheme_updated", {
        "scheme_code": scheme_code, "from_status": before, "to_status": body.status,
        "last_verified_at": row.last_verified_at,
    })
    return scheme_row(get_scheme_any(scheme_code), (_file_scheme(scheme_code) or {}).get("status", ""), True)


@router.delete("/schemes/{scheme_code}/override")
def remove_override(scheme_code: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Go back to exactly what schemes.json says for this scheme."""
    row = db.get(SchemeOverride, scheme_code)
    if not row:
        raise HTTPException(404, "This scheme has no administrator changes")
    db.delete(row)
    db.commit()
    refresh_overrides(db)
    log_event(db, admin.id, "admin_override_removed", {"scheme_code": scheme_code})
    return scheme_row(get_scheme_any(scheme_code), (_file_scheme(scheme_code) or {}).get("status", ""), False)


@router.get("/coverage")
def coverage(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return coverage_report(db)


@router.post("/schemes/validate")
def validate(body: ValidateRequest, admin: User = Depends(require_admin)):
    errors, warnings = validate_scheme_dict(body.scheme)
    return {"valid": not errors, "errors": errors, "warnings": warnings}


@router.get("/audit")
def recent_activity(limit: int = Query(100, ge=1, le=500), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Recent events from all accounts. Users appear only as numbers, never by name or e-mail."""
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return [{"id": r.id, "userId": r.user_id, "event": r.event_type, "payload": r.payload, "createdAt": r.created_at} for r in rows]
