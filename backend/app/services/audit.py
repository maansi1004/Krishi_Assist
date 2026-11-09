"""Writes the audit trail (the audit_logs table).

Rules this file keeps:
* It never stops a request. If writing the log fails, the problem is printed to the
  server log and the farmer's action still goes through.
* Payloads hold only facts about WHAT happened (scheme code, old and new status,
  which profile fields changed). They never hold passwords, e-mail addresses or the
  farmer's profile values.
"""
from __future__ import annotations

import logging

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def log_event(db, user_id: int | None, event_type: str, payload: dict | None = None) -> None:
    try:
        db.add(AuditLog(user_id=user_id, event_type=event_type, payload=payload or {}))
        db.commit()
    except Exception:  # noqa: BLE001 - the audit trail must never break the request
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        logger.exception("Could not write audit event %s", event_type)
