"""A farmer's own document vault: upload, list, view, download, edit, delete, and a
per-scheme plan that shows which required documents are already uploaded, what the farmer
still has to arrange, and how to get each missing document.

Safety rules kept here:
* Every route needs a signed-in farmer, and a farmer can only ever see or change their OWN files.
  Someone else's document answers "not found", the same as a document that does not exist.
* The file is checked by its real content (PDF, JPEG or PNG only), its size is limited while it
  is being received, and per-farmer limits apply (number of files, total size, uploads per hour).
* The API never reveals where a file is stored on disk.
* Audit entries record what kind of document and how big, never the file name or its contents.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document, DocumentChoice
from app.models.user import User
from app.services.audit import log_event
from app.services.document_storage import get_storage
from app.services.document_types import DOCUMENT_TYPES, TYPE_IDS, satisfying_types, suggest_type, used_by_schemes
from app.services.how_to_get import how_to_get
from app.services.rate_limit import upload_limiter
from app.services.scheme_service import get_scheme, load_schemes
from app.services.upload_checks import ALLOWED, UploadTooLarge, clean_filename, read_limited, sniff_type

router = APIRouter(prefix="/api/documents", tags=["documents"])
MB = 1024 * 1024
REQUIRED_ORDER = {"required": 0, "conditional": 1, "verification": 2}


def _meta(row: Document) -> dict:
    return {
        "id": row.id, "docType": row.doc_type, "name": row.original_name, "contentType": row.content_type,
        "sizeBytes": row.size_bytes, "note": row.note, "uploadedAt": row.uploaded_at,
    }


def _owned(db: Session, user: User, doc_id: int) -> Document:
    row = db.query(Document).filter_by(id=doc_id, user_id=user.id).first()
    if not row:
        raise HTTPException(404, "Document not found")
    return row


def _limits() -> dict:
    return {"maxFileBytes": settings.max_upload_mb * MB, "maxDocuments": settings.max_documents_per_user,
            "maxTotalBytes": settings.max_storage_mb_per_user * MB, "allowed": ["PDF", "JPEG", "PNG"]}


def _usage(db: Session, user: User) -> dict:
    count, used = db.query(func.count(Document.id), func.coalesce(func.sum(Document.size_bytes), 0)).filter(Document.user_id == user.id).one()
    return {"count": int(count), "bytes": int(used)}


@router.get("/types")
def types():
    """The kinds of document a farmer can choose from, and how many schemes ask for each.
    There is no personal data here."""
    counts = used_by_schemes(load_schemes())
    return [{**t, "usedBySchemes": counts.get(t["id"], 0)} for t in DOCUMENT_TYPES]


@router.get("")
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Document).filter_by(user_id=user.id).order_by(Document.id.desc()).all()
    return {"documents": [_meta(r) for r in rows], "usage": _usage(db, user), "limits": _limits()}


@router.post("", status_code=201)
async def upload(
    request: Request,
    doc_type: str = Query(...),
    filename: str = Query("", max_length=255),
    note: str | None = Query(None, max_length=300),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """The file is sent as the request body itself (no form wrapper), with the details in the address."""
    key = str(user.id)
    upload_limiter.check(key, "upload")
    upload_limiter.record(key)

    if doc_type not in TYPE_IDS:
        raise HTTPException(422, "Unknown document type")
    max_file = settings.max_upload_mb * MB
    too_big = HTTPException(413, f"The file is larger than {settings.max_upload_mb} MB")
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > max_file:
        raise too_big
    usage = _usage(db, user)
    if usage["count"] >= settings.max_documents_per_user:
        raise HTTPException(409, f"You can keep up to {settings.max_documents_per_user} documents. Delete one first.")

    try:
        data = await read_limited(request.stream(), max_file)
    except UploadTooLarge:
        raise too_big
    if not data:
        raise HTTPException(422, "The file is empty")
    content_type = sniff_type(data)
    if not content_type:
        raise HTTPException(415, "Only PDF, JPEG or PNG files are accepted")
    if usage["bytes"] + len(data) > settings.max_storage_mb_per_user * MB:
        raise HTTPException(413, f"This would go over your storage limit of {settings.max_storage_mb_per_user} MB")

    digest = hashlib.sha256(data).hexdigest()
    if db.query(Document.id).filter_by(user_id=user.id, sha256=digest).first():
        raise HTTPException(409, "You have already uploaded this exact file")

    storage = get_storage()
    stored_name = storage.save(user.id, data, ALLOWED[content_type])
    row = Document(
        user_id=user.id, doc_type=doc_type, original_name=clean_filename(filename, content_type), stored_name=stored_name,
        content_type=content_type, size_bytes=len(data), sha256=digest, note=(note or "").strip() or None,
    )
    try:
        db.add(row)
        db.commit()
    except IntegrityError:           # the same file arrived twice at the same moment
        db.rollback()
        storage.delete(user.id, stored_name)
        raise HTTPException(409, "You have already uploaded this exact file")
    except Exception:
        db.rollback()
        storage.delete(user.id, stored_name)   # never leave a file behind without a record
        raise
    db.refresh(row)
    meta = _meta(row)
    log_event(db, user.id, "document_uploaded", {"doc_type": doc_type, "size_bytes": meta["sizeBytes"], "content_type": content_type})
    return meta


@router.get("/checklist/{scheme_code}")
def checklist(scheme_code: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The documents a scheme asks for, and which of them this farmer has already uploaded."""
    scheme = get_scheme(scheme_code)
    if not scheme:
        raise HTTPException(404, "Scheme not found")
    have: dict[str, list[int]] = {}
    for doc_id, doc_type in db.query(Document.id, Document.doc_type).filter_by(user_id=user.id).all():
        have.setdefault(doc_type, []).append(doc_id)
    items = []
    for d in scheme.get("documents", []):
        suggested = suggest_type(d["name"])
        matchable = suggested != "other"
        ids = [i for t in satisfying_types(suggested) for i in have.get(t, [])] if matchable else []
        items.append({"name": d["name"], "purpose": d.get("purpose"), "requiredType": d.get("requiredType"),
                      "suggestedType": suggested, "matchable": matchable, "uploaded": bool(ids), "documentIds": ids})
    required = [i for i in items if i["requiredType"] == "required" and i["matchable"]]
    return {"schemeCode": scheme_code, "items": items,
            "summary": {"requiredChecked": len(required), "requiredUploaded": sum(1 for i in required if i["uploaded"])}}


def _plan(db: Session, user: User, scheme: dict) -> dict:
    """For one scheme: every document it asks for, with what the farmer has done about it.

    status:  ready          a matching file is uploaded
             ready_self     the farmer says they have it (nothing to upload)
             not_applicable the farmer says it does not apply to them
             to_arrange     the farmer does not have it yet  -> next steps are shown
             undecided      the farmer has not answered yet
    """
    have: dict[str, list[int]] = {}
    for doc_id, doc_type in db.query(Document.id, Document.doc_type).filter_by(user_id=user.id).all():
        have.setdefault(doc_type, []).append(doc_id)
    choices = {c.document_name: c.choice for c in db.query(DocumentChoice).filter_by(user_id=user.id, scheme_code=scheme["schemeCode"]).all()}

    items = []
    for d in scheme.get("documents", []):
        suggested = suggest_type(d["name"])
        matchable = suggested != "other"
        ids = [i for t in satisfying_types(suggested) for i in have.get(t, [])] if matchable else []
        choice = choices.get(d["name"])
        if ids:
            status = "ready"
        elif choice == "have_it":
            status = "ready_self"
        elif choice == "not_applicable":
            status = "not_applicable"
        elif choice == "dont_have":
            status = "to_arrange"
        else:
            status = "undecided"
        items.append({
            "name": d["name"], "purpose": d.get("purpose"), "requiredType": d.get("requiredType"), "suggestedType": suggested,
            "matchable": matchable, "status": status, "choice": choice, "documentIds": ids,
            "howToGet": how_to_get(suggested) if status in ("to_arrange", "undecided") else None,
        })

    def count(status_set, only_required=False):
        return sum(1 for i in items if i["status"] in status_set and (not only_required or i["requiredType"] == "required"))

    next_steps = sorted((i for i in items if i["status"] == "to_arrange"),
                        key=lambda i: (REQUIRED_ORDER.get(i["requiredType"], 3), i["name"]))
    return {
        "schemeCode": scheme["schemeCode"],
        "summary": {
            "total": len(items), "ready": count({"ready", "ready_self"}), "notApplicable": count({"not_applicable"}),
            "toArrange": count({"to_arrange"}), "undecided": count({"undecided"}),
            "required": sum(1 for i in items if i["requiredType"] == "required"),
            "requiredReady": count({"ready", "ready_self"}, True), "requiredOpen": count({"to_arrange", "undecided"}, True),
        },
        "items": items,
        "nextSteps": [{"name": i["name"], "suggestedType": i["suggestedType"], "requiredType": i["requiredType"], "howToGet": i["howToGet"]} for i in next_steps],
    }


@router.get("/plan/{scheme_code}")
def document_plan(scheme_code: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The document part of "Plan application" for one scheme."""
    scheme = get_scheme(scheme_code)
    if not scheme:
        raise HTTPException(404, "Scheme not found")
    return _plan(db, user, scheme)


class PlanChoice(BaseModel):
    document_name: str = Field(min_length=1, max_length=200)
    choice: Literal["have_it", "dont_have", "not_applicable"] | None = None   # None clears the answer


@router.put("/plan/{scheme_code}")
def set_plan_choice(scheme_code: str, body: PlanChoice, user: User = Depends(current_user), db: Session = Depends(get_db)):
    scheme = get_scheme(scheme_code)
    if not scheme:
        raise HTTPException(404, "Scheme not found")
    if body.document_name not in {d["name"] for d in scheme.get("documents", [])}:
        raise HTTPException(422, "This scheme does not ask for that document")
    row = db.query(DocumentChoice).filter_by(user_id=user.id, scheme_code=scheme_code, document_name=body.document_name).first()
    if body.choice is None:
        if row:
            db.delete(row)
    elif row:
        row.choice = body.choice
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(DocumentChoice(user_id=user.id, scheme_code=scheme_code, document_name=body.document_name, choice=body.choice))
    db.commit()
    log_event(db, user.id, "document_plan_updated", {"scheme_code": scheme_code, "choice": body.choice or "cleared"})
    return _plan(db, user, scheme)


@router.get("/{doc_id}/file")
def get_file(doc_id: int, download: bool = Query(False), user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = _owned(db, user, doc_id)
    storage = get_storage()
    if not storage.exists(row.user_id, row.stored_name):
        raise HTTPException(404, "The stored file is missing. Please upload it again.")
    path = storage.path_for(row.user_id, row.stored_name)
    safe_ascii = re.sub(r"[^A-Za-z0-9._ -]", "_", row.original_name)
    kind = "attachment" if download else "inline"
    headers = {
        "Content-Disposition": f"{kind}; filename=\"{safe_ascii}\"; filename*=UTF-8''{quote(row.original_name, safe='')}",
        "X-Content-Type-Options": "nosniff",      # the browser must trust our type, not guess its own
        "Cache-Control": "private, no-store",     # personal documents are never kept in shared caches
        "X-Frame-Options": "DENY",
    }
    if download:
        log_event(db, user.id, "document_downloaded", {"doc_type": row.doc_type})
    return FileResponse(path, media_type=row.content_type, headers=headers)


class DocumentUpdate(BaseModel):
    doc_type: str | None = None
    note: str | None = Field(default=None, max_length=300)


@router.patch("/{doc_id}")
def update_document(doc_id: int, body: DocumentUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = _owned(db, user, doc_id)
    if body.doc_type is not None:
        if body.doc_type not in TYPE_IDS:
            raise HTTPException(422, "Unknown document type")
        row.doc_type = body.doc_type
    if "note" in body.model_fields_set:
        row.note = (body.note or "").strip() or None
    db.commit()
    db.refresh(row)
    return _meta(row)


@router.delete("/{doc_id}")
def delete_document(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = _owned(db, user, doc_id)
    doc_type, user_id, stored_name = row.doc_type, row.user_id, row.stored_name
    db.delete(row)
    db.commit()
    get_storage().delete(user_id, stored_name)
    log_event(db, user.id, "document_deleted", {"doc_type": doc_type})
    return {"deleted": True}
