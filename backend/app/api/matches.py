"""Check ONE saved farm profile against ALL schemes and group the answers.

This is the "rule engine evaluates active schemes against profile" step of the
activity diagram. The eligibility decision itself still comes only from the rule
engine; this file just runs it for every scheme and sorts the results.
Nothing is written to the evaluation history here (one click on a scheme does that).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user
from app.db.session import get_db
from app.engines.eligibility_engine import evaluate_scheme
from app.engines.recommendation_engine import score_scheme
from app.models.profile import FarmProfile
from app.models.user import User
from app.schemas.profile import FarmerProfile
from app.services.profile_service import profile_completeness, profile_to_dict
from app.services.scheme_service import load_schemes

router = APIRouter(prefix="/api/matches", tags=["matches"])

STATUS_ORDER = ["ELIGIBLE", "ALMOST_ELIGIBLE", "VERIFICATION_REQUIRED", "NOT_ELIGIBLE"]


def _state_fit(scheme: dict, profile: dict) -> int:
    """2 = the farmer's own state, 1 = All India, 0 = another state or unknown."""
    farmer_state = str(profile.get("state") or "").strip().lower()
    scheme_state = str(scheme.get("state") or "").strip().lower()
    if farmer_state and scheme_state == farmer_state:
        return 2
    return 1 if scheme_state in ("all india", "") else 0


def _sentences(result: dict, fields: list[str]) -> list[str]:
    """Raw field names -> the rule's plain sentence."""
    by_field: dict[str, str] = {}
    for c in result.get("criteria", []) + result.get("exclusions", []) + result.get("verificationCriteria", []):
        by_field.setdefault(c["field"], (c.get("criterion") or c["field"].replace("_", " ")).rstrip(" ."))
    return [by_field.get(f, f.replace("_", " ")) for f in fields]


def _summary(scheme: dict, result: dict, profile: dict) -> dict:
    everything = result["criteria"] + result["exclusions"] + result["verificationCriteria"]
    unknown = [c for c in everything if c["result"] == "UNKNOWN"]
    questions = {c["field"] for c in unknown if c.get("source") == "extra_attributes"}
    profile_gaps = sorted({c["field"] for c in unknown if c.get("source") != "extra_attributes"})
    failed = _sentences(result, result["failedRequirements"])
    farmer_state = str(profile.get("state") or "").strip().lower()
    scheme_state = str(scheme.get("state") or "").strip().lower()
    return {
        "schemeCode": scheme["schemeCode"],
        "name": scheme["name"],
        "state": scheme.get("state"),
        "category": scheme.get("category"),
        "status": result["status"],
        "unverifiedScheme": result["unverifiedScheme"],
        "passed": sum(1 for c in result["criteria"] if c["result"] == "PASS"),
        "total": len(result["criteria"]),
        "reason": failed[0] if failed else None,
        "questionsToAnswer": len(questions),
        "profileFieldsMissing": profile_gaps,
        "otherState": bool(farmer_state) and scheme_state not in ("", "all india") and scheme_state != farmer_state,
    }


def build_matches(profile: dict, schemes: list[dict], profile_used: bool = True, need_text: str | None = None) -> dict:
    """Run the rule engine for every scheme and group the answers.

    If the farmer described a need, every item also gets a needScore (0-100, how well the
    scheme fits the words they used) and the best fits are listed first in bestForNeed.
    The need only changes the ORDER. It never changes an eligibility result.
    """
    groups: dict[str, list[dict]] = {status: [] for status in STATUS_ORDER}
    if profile_used:
        for scheme in schemes:
            result = evaluate_scheme(scheme, profile)
            item = _summary(scheme, result, profile)
            item["needScore"] = score_scheme(scheme, need_text, profile) if need_text else 0
            item["_sort"] = (-item["needScore"], -_state_fit(scheme, profile), scheme.get("status") != "active", -item["passed"], scheme["schemeCode"])
            groups[result["status"]].append(item)
        for items in groups.values():
            items.sort(key=lambda i: i["_sort"])
        order = {status: n for n, status in enumerate(STATUS_ORDER)}
        best = []
        if need_text:
            candidates = [i for status in STATUS_ORDER[:3] for i in groups[status] if i["needScore"] >= 35]
            candidates.sort(key=lambda i: (-i["needScore"], order[i["status"]], i["schemeCode"]))
            best = [dict(i) for i in candidates[:5]]
        for items in groups.values():
            for i in items:
                i.pop("_sort", None)
        for i in best:
            i.pop("_sort", None)
    else:
        best = []

    return {
        "profileUsed": profile_used,
        "profileCompleteness": profile_completeness(profile, schemes),
        "schemeCount": len(schemes),
        "counts": {status: len(items) for status, items in groups.items()},
        "groups": groups,
        "bestForNeed": best,
    }


@router.get("/completeness")
def completeness(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_to_dict(db.query(FarmProfile).filter_by(user_id=user.id).first())
    return profile_completeness(profile, load_schemes())


@router.get("")
def my_matches(user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(FarmProfile).filter_by(user_id=user.id).first()
    return build_matches(profile_to_dict(row), load_schemes(), profile_used=bool(row))


class PreviewRequest(BaseModel):
    profile: FarmerProfile
    need_text: str | None = Field(default=None, max_length=1000)


@router.post("/preview")
def preview_matches(request: PreviewRequest, user: User = Depends(current_user)):
    """Same grouped answer as GET /api/matches, but for a profile the farmer has just confirmed
    on screen (not necessarily saved). Nothing is stored."""
    need = (request.need_text or "").strip() or None
    return build_matches(request.profile.model_dump(), load_schemes(), profile_used=True, need_text=need)
