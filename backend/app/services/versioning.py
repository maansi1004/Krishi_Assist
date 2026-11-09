"""Version information stored with every saved evaluation.

* scheme_version: the date the scheme data was last checked against the official
  source (``lastVerifiedAt`` in schemes.json), or "unverified" when nobody has set it.
* rule_version: a short fingerprint of the scheme's rules. If anyone edits the
  eligibility, exclusion or verification rules, the fingerprint changes, so an old
  evaluation can always be recognised as "made with the older rules".
"""
from __future__ import annotations

import hashlib
import json

RULE_KEYS = ("eligibility", "exclusions", "verificationConditions")


def rule_fingerprint(scheme: dict) -> str:
    rules = {key: scheme.get(key) for key in RULE_KEYS}
    blob = json.dumps(rules, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def scheme_version(scheme: dict) -> str:
    return scheme.get("lastVerifiedAt") or "unverified"
