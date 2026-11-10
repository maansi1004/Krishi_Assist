"""Where uploaded files are kept on disk.

Layout:  <upload folder>/<user id>/<random name>.<pdf|jpg|png>

* The folder is outside the website files, so a file can never be fetched by guessing a URL.
  Files are only served by the API, after checking who is asking.
* Names are random and made here. A path is checked to be inside the upload folder before it is used.
* This is plain local storage. The files are NOT encrypted on disk (see SECURITY_NOTES.md).
  To use encrypted or cloud storage later, only this file needs to change.
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from app.core.config import settings

NAME_RE = re.compile(r"^[0-9a-f]{32}\.(pdf|jpg|png)$")


class LocalStorage:
    def __init__(self, base: Path):
        self.base = Path(base).resolve()

    def path_for(self, user_id: int, stored_name: str) -> Path:
        if not NAME_RE.match(stored_name or ""):
            raise ValueError("invalid stored name")
        path = (self.base / str(int(user_id)) / stored_name).resolve()
        if self.base not in path.parents:
            raise ValueError("path outside the upload folder")
        return path

    def save(self, user_id: int, data: bytes, ext: str) -> str:
        stored_name = f"{uuid.uuid4().hex}{ext}"
        path = self.path_for(user_id, stored_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".part")
        with open(temp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass  # not supported on every system (for example Windows)
        os.replace(temp, path)  # the file appears complete or not at all
        return stored_name

    def exists(self, user_id: int, stored_name: str) -> bool:
        try:
            return self.path_for(user_id, stored_name).is_file()
        except ValueError:
            return False

    def delete(self, user_id: int, stored_name: str) -> None:
        try:
            self.path_for(user_id, stored_name).unlink(missing_ok=True)
        except ValueError:
            pass


_storage: LocalStorage | None = None


def get_storage() -> LocalStorage:
    global _storage
    if _storage is None or _storage.base != Path(settings.upload_path).resolve():
        _storage = LocalStorage(settings.upload_path)
    return _storage
