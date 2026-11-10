"""Checks on an uploaded file. We trust the CONTENT of the file, never its name or the
Content-Type the browser claims, because both are easy to fake."""
from __future__ import annotations

import os
import re
import unicodedata

ALLOWED = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}


class UploadTooLarge(Exception):
    pass


def sniff_type(data: bytes) -> str | None:
    """The real type of the file from its first bytes, or None when it is not a PDF, JPEG or PNG."""
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def clean_filename(raw: str | None, content_type: str) -> str:
    """A safe name to SHOW the farmer. Folders, odd characters and fake extensions are removed,
    and the extension always matches what the file really is."""
    ext = ALLOWED[content_type]
    name = (raw or "").replace("\\", "/").split("/")[-1]
    name = unicodedata.normalize("NFKC", name)
    name = "".join(ch for ch in name if ch.isprintable() and ch not in '<>:"|?*')
    name = re.sub(r"\s+", " ", name).strip(" .")
    stem = os.path.splitext(name)[0].strip(" .")[:80].strip(" .")
    return (stem or "document") + ext


async def read_limited(chunks, max_bytes: int) -> bytes:
    """Read the request body piece by piece and stop as soon as it is too big, so a huge upload
    never fills the server's memory."""
    buffer = bytearray()
    async for chunk in chunks:
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise UploadTooLarge()
    return bytes(buffer)
