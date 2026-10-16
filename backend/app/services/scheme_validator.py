from __future__ import annotations

import json
from pathlib import Path
from jsonschema import Draft202012Validator

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
SCHEMA_FILE = DATA_DIR / "scheme.schema.json"
SCHEMES_FILE = DATA_DIR / "schemes.json"


def validate_schemes() -> list[str]:
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    schemes = json.loads(SCHEMES_FILE.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors: list[str] = []

    if not isinstance(schemes, list):
        return ["schemes.json must contain a JSON array"]

    codes: set[str] = set()
    for index, scheme in enumerate(schemes):
        code = scheme.get("schemeCode", f"index-{index}") if isinstance(scheme, dict) else f"index-{index}"
        if code in codes:
            errors.append(f"Duplicate schemeCode: {code}")
        codes.add(code)
        for error in sorted(validator.iter_errors(scheme), key=lambda e: list(e.path)):
            path = ".".join(str(x) for x in error.path) or "root"
            errors.append(f"{code}.{path}: {error.message}")

    return errors


if __name__ == "__main__":
    errors = validate_schemes()
    if errors:
        print("SCHEME VALIDATION FAILED")
        print("\n".join(errors))
        raise SystemExit(1)
    print("SCHEME VALIDATION PASSED")
