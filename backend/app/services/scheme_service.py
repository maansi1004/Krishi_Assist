import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[3] / "data/schemes.json"
DATA_FILE = DATA_FILE.resolve()

# The scheme file is about 160 KB. Reading and parsing it on every call made the
# assistant do the same work several times per message. We keep one copy in memory
# and reload it automatically only when schemes.json changes on disk.
_cache: dict = {"mtime": None, "data": []}


def load_schemes() -> list[dict]:
    mtime = DATA_FILE.stat().st_mtime
    if _cache["mtime"] != mtime:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            _cache["data"] = json.load(f)
        _cache["mtime"] = mtime
    return _cache["data"]


def get_scheme(code: str) -> dict | None:
    return next((s for s in load_schemes() if s["schemeCode"] == code), None)
