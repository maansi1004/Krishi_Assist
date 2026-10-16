import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[3] / "data/schemes.json"
DATA_FILE = DATA_FILE.resolve()


def load_schemes() -> list[dict]:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_scheme(code: str) -> dict | None:
    return next((s for s in load_schemes() if s["schemeCode"] == code), None)
