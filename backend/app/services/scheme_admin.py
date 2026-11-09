"""Everything the administrator screens need: reading overrides, summaries, the coverage
report, and checking a new scheme file against the JSON schema."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

from jsonschema import Draft202012Validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.evaluation import Evaluation
from app.models.profile import FarmProfile
from app.models.saved_scheme import SavedScheme
from app.models.scheme_override import SchemeOverride
from app.models.user import User
from app.services.need_extraction import INDIAN_STATES
from app.services.scheme_service import get_scheme_any, load_all_schemes, load_file_schemes, set_overrides
from app.services.scheme_validator import SCHEMA_FILE

STALE_AFTER_DAYS = 180


def refresh_overrides(db: Session) -> None:
    rows = db.query(SchemeOverride).all()
    set_overrides({r.scheme_code: {"status": r.status, "lastVerifiedAt": r.last_verified_at} for r in rows})


def _leaves(rule: dict):
    if "conditions" in rule:
        for child in rule["conditions"]:
            yield from _leaves(child)
    else:
        yield rule


def criteria_count(scheme: dict) -> int:
    return len(list(_leaves(scheme.get("eligibility") or {"conditions": []})))


def scheme_row(scheme: dict, file_status: str, overridden: bool) -> dict:
    sources = scheme.get("sources") or []
    return {
        "schemeCode": scheme["schemeCode"], "name": scheme["name"], "state": scheme.get("state"),
        "category": scheme.get("category"), "status": scheme.get("status"), "fileStatus": file_status,
        "lastVerifiedAt": scheme.get("lastVerifiedAt"), "overridden": overridden,
        "criteriaCount": criteria_count(scheme), "sourceCount": len(sources),
        "sourcesWithUrl": sum(1 for s in sources if s.get("url")),
    }


def list_scheme_rows(db: Session) -> list[dict]:
    overridden = {r.scheme_code for r in db.query(SchemeOverride.scheme_code).all()}
    file_status = {s["schemeCode"]: s.get("status") for s in load_file_schemes()}
    return [scheme_row(s, file_status.get(s["schemeCode"], ""), s["schemeCode"] in overridden) for s in load_all_schemes()]


def _parse_date(value) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def coverage_report(db: Session, today: date | None = None) -> dict:
    today = today or datetime.now(timezone.utc).date()
    schemes = load_all_schemes()
    by_status: dict[str, int] = {}
    by_state: dict[str, dict] = {}
    by_category: dict[str, int] = {}
    never, stale, no_url, hindi_missing, single_rule = [], [], [], [], []
    for s in schemes:
        code = s["schemeCode"]
        by_status[s.get("status", "unknown")] = by_status.get(s.get("status", "unknown"), 0) + 1
        st = by_state.setdefault(s.get("state") or "Unknown", {"total": 0, "active": 0})
        st["total"] += 1
        st["active"] += 1 if s.get("status") == "active" else 0
        by_category[s.get("category") or "unknown"] = by_category.get(s.get("category") or "unknown", 0) + 1
        verified = _parse_date(s.get("lastVerifiedAt"))
        if not verified:
            never.append(code)
        elif (today - verified).days > STALE_AFTER_DAYS:
            stale.append(code)
        if not any(src.get("url") for src in (s.get("sources") or [])):
            no_url.append(code)
        hi = (s.get("translations") or {}).get("hi") or {}
        if not hi.get("description") or hi.get("description") == s.get("description"):
            hindi_missing.append(code)
        if criteria_count(s) <= 1:
            single_rule.append(code)
    covered = {s.get("state") for s in schemes}
    return {
        "totals": {"schemes": len(schemes), **{k: v for k, v in sorted(by_status.items())}},
        "byState": dict(sorted(by_state.items())),
        "byCategory": dict(sorted(by_category.items())),
        "gaps": {
            "neverVerified": never, "staleVerification": stale, "noSourceUrl": no_url,
            "hindiMissing": hindi_missing, "singleRuleOnly": single_rule,
        },
        "statesWithoutSchemes": [s for s in INDIAN_STATES if s not in covered],
        "staleAfterDays": STALE_AFTER_DAYS,
        "usage": {
            "farmers": db.query(func.count(User.id)).filter(User.role == "farmer").scalar() or 0,
            "profiles": db.query(func.count(FarmProfile.id)).scalar() or 0,
            "evaluations": db.query(func.count(Evaluation.id)).scalar() or 0,
            "applications": db.query(func.count(Application.id)).scalar() or 0,
            "savedSchemes": db.query(func.count(SavedScheme.id)).scalar() or 0,
        },
    }


def validate_scheme_dict(scheme) -> tuple[list[str], list[str]]:
    """(errors, warnings) for one scheme record, using the same JSON schema as schemes.json."""
    if not isinstance(scheme, dict):
        return ["The scheme must be a JSON object."], []
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    errors = []
    for error in sorted(Draft202012Validator(schema).iter_errors(scheme), key=lambda e: list(e.path)):
        errors.append(f"{'.'.join(str(x) for x in error.path) or 'root'}: {error.message}")
    warnings = []
    code = scheme.get("schemeCode")
    if code and get_scheme_any(code):
        warnings.append(f"A scheme with code {code} already exists. Using this code would replace it.")
    if not errors and criteria_count(scheme) <= 1:
        warnings.append("Only one eligibility rule. Check that the official guideline has no other conditions.")
    return errors, warnings
