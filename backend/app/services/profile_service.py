"""Small helpers about the saved farm profile that several routes need."""
from __future__ import annotations

from typing import Any

from app.schemas.profile import FarmerProfile

PROFILE_FIELDS = list(FarmerProfile.model_fields.keys())

# The fields scheme rules look at most often come first, so the "please fill in" list
# starts with the things that matter most. Fields not listed here follow alphabetically.
PRIORITY = [
    "state", "farmer_type", "land_size_hectares", "age", "social_category",
    "primary_crop", "bank_account_status", "kcc_holder", "years_of_cultivation",
]

LABELS = {
    "state": "State", "farmer_type": "Farmer type", "land_size_hectares": "Land size (hectares)",
    "age": "Age", "social_category": "Social category", "primary_crop": "Main crop",
    "bank_account_status": "Bank account", "kcc_holder": "Kisan Credit Card",
    "years_of_cultivation": "Years of farming",
}


def profile_to_dict(row: Any) -> dict:
    """The saved profile row as a plain dict (empty if the farmer has not saved one yet)."""
    if not row:
        return {}
    return {f: getattr(row, f) for f in PROFILE_FIELDS}


def _walk(rule: dict, out: set[str]) -> None:
    if "conditions" in rule:
        for child in rule["conditions"]:
            _walk(child, out)
    elif rule.get("fieldSource", "profile") == "profile" and rule.get("fieldName"):
        out.add(rule["fieldName"])


def profile_fields_used_by_rules(schemes: list[dict]) -> list[str]:
    """Every normal profile field that at least one scheme rule looks at."""
    used: set[str] = set()
    for scheme in schemes:
        for key in ("eligibility", "exclusions"):
            if scheme.get(key):
                _walk(scheme[key], used)
        for rule in scheme.get("verificationConditions", []):
            _walk(rule, used)
    first = [f for f in PRIORITY if f in used]
    return first + sorted(used - set(first))


def _is_filled(value: Any) -> bool:
    # False and 0 are real answers (for example "no Kisan Credit Card"); only blank means missing.
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def profile_completeness(profile: dict, schemes: list[dict]) -> dict:
    fields = profile_fields_used_by_rules(schemes)
    missing = [f for f in fields if not _is_filled(profile.get(f))]
    total = len(fields)
    filled = total - len(missing)
    return {
        "total": total,
        "filled": filled,
        "percent": round(100 * filled / total) if total else 100,
        "complete": not missing,
        "missing": [{"field": f, "label": LABELS.get(f, f.replace("_", " ").capitalize())} for f in missing],
    }
