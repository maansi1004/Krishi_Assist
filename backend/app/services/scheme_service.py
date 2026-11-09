import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[3] / "data/schemes.json"
DATA_FILE = DATA_FILE.resolve()
INACTIVE = "inactive"

# The scheme file is about 160 KB. We keep one copy in memory and reload it automatically
# only when schemes.json changes on disk, or when an administrator changes a scheme.
_file_cache: dict = {"mtime": None, "data": []}
_merged_cache: dict = {"key": None, "all": [], "visible": []}
_overrides: dict[str, dict] = {}
_overrides_version = 0


def set_overrides(rows: dict[str, dict]) -> None:
    """Install the administrator's decisions: {scheme_code: {"status": ..., "lastVerifiedAt": ...}}."""
    global _overrides, _overrides_version
    _overrides = dict(rows)
    _overrides_version += 1


def load_file_schemes() -> list[dict]:
    """The schemes exactly as written in schemes.json (no administrator changes)."""
    mtime = DATA_FILE.stat().st_mtime
    if _file_cache["mtime"] != mtime:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            _file_cache["data"] = json.load(f)
        _file_cache["mtime"] = mtime
    return _file_cache["data"]


def _rebuild() -> None:
    raw = load_file_schemes()
    key = (_file_cache["mtime"], _overrides_version)
    if _merged_cache["key"] == key:
        return
    merged = []
    for scheme in raw:
        override = _overrides.get(scheme["schemeCode"])
        if override:
            scheme = dict(scheme)  # never change the cached original
            scheme["status"] = override["status"]
            if override.get("lastVerifiedAt"):
                scheme["lastVerifiedAt"] = override["lastVerifiedAt"]
        merged.append(scheme)
    _merged_cache.update(key=key, all=merged, visible=[s for s in merged if s.get("status") != INACTIVE])


def load_all_schemes() -> list[dict]:
    """Every scheme with administrator changes applied, including switched-off ones."""
    _rebuild()
    return _merged_cache["all"]


def load_schemes() -> list[dict]:
    """The schemes farmers can see: everything except switched-off schemes."""
    _rebuild()
    return _merged_cache["visible"]


def get_scheme(code: str) -> dict | None:
    return next((s for s in load_schemes() if s["schemeCode"] == code), None)


def get_scheme_any(code: str) -> dict | None:
    return next((s for s in load_all_schemes() if s["schemeCode"] == code), None)
