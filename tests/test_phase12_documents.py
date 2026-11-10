import json
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.document import Document
from app.services.document_storage import NAME_RE, LocalStorage, get_storage
from app.services.document_types import DOCUMENT_TYPES, satisfying_types, suggest_type
from app.services.rate_limit import upload_limiter
from app.services.upload_checks import clean_filename, sniff_type

client = TestClient(app)
MB = 1024 * 1024


def pdf(tag="") -> bytes:
    return b"%PDF-1.4\n% test file " + (tag or uuid.uuid4().hex).encode() + b"\n%%EOF\n"


def jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0\x00\x10JFIF" + os.urandom(64)


def png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + os.urandom(64)


def farmer():
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"name": "Test Farmer", "email": email, "password": "StrongPass123"}).json()
    return {"Authorization": f"Bearer {r['access_token']}"}


def upload(headers, data=None, doc_type="land_record", filename="khasra.pdf", note=None, content_type="application/octet-stream"):
    params = {"doc_type": doc_type, "filename": filename}
    if note is not None:
        params["note"] = note
    return client.post("/api/documents", params=params, content=pdf() if data is None else data, headers={**headers, "Content-Type": content_type})


def audit(headers, event):
    return [e for e in client.get("/api/audit?limit=200", headers=headers).json() if e["event"] == event]


def test_document_types_are_offered_in_three_languages():
    types = client.get("/api/documents/types").json()
    assert len(types) == len(DOCUMENT_TYPES) >= 10
    assert all(set(t["label"]) == {"en", "hi", "hinglish"} and all(t["label"].values()) for t in types)
    assert {"aadhaar", "land_record", "bank_passbook", "other"} <= {t["id"] for t in types}


def test_pdf_jpeg_and_png_are_accepted_and_described():
    h = farmer()
    for data, ctype, ext in [(pdf(), "application/pdf", ".pdf"), (jpeg(), "image/jpeg", ".jpg"), (png(), "image/png", ".png")]:
        r = upload(h, data, filename="my scan.jpeg", note="  front side ")
        assert r.status_code == 201, r.text
        meta = r.json()
        assert meta["contentType"] == ctype and meta["name"] == "my scan" + ext and meta["sizeBytes"] == len(data)
        assert meta["note"] == "front side" and meta["docType"] == "land_record"
        assert "storedName" not in meta and "stored_name" not in meta and "path" not in json.dumps(meta).lower()
    listing = client.get("/api/documents", headers=h).json()
    assert len(listing["documents"]) == 3 and listing["usage"]["count"] == 3
    assert listing["limits"]["maxFileBytes"] == 5 * MB


def test_the_real_content_decides_the_type_not_the_name_or_the_header():
    h = farmer()
    meta = upload(h, pdf(), filename="photo.png", content_type="image/png").json()
    assert meta["contentType"] == "application/pdf" and meta["name"] == "photo.pdf"


@pytest.mark.parametrize("data", [
    b"just some text pretending to be a document",
    b"MZ\x90\x00\x03\x00\x00\x00 a program, not a document",
    b"<html><script>alert(1)</script></html>",
    b"PK\x03\x04 a zip archive",
    b"GIF89a not on the allowed list",
    b" %PDF-1.4 leading space is not a real PDF start",
])
def test_files_that_are_not_pdf_jpeg_or_png_are_refused(data):
    h = farmer()
    r = upload(h, data, filename="document.pdf", content_type="application/pdf")
    assert r.status_code == 415 and "PDF, JPEG or PNG" in r.json()["detail"]
    assert client.get("/api/documents", headers=h).json()["documents"] == []


def test_empty_files_and_unknown_types_and_signed_out_visitors_are_refused():
    h = farmer()
    assert upload(h, b"").status_code == 422
    assert upload(h, doc_type="passwords").status_code == 422
    r = client.post("/api/documents", params={"doc_type": "other"}, content=pdf())
    assert r.status_code in (401, 403)


def test_the_size_limit_is_enforced_for_declared_and_streamed_bodies():
    h = farmer()
    just_right = b"%PDF-1.4\n" + b"0" * (5 * MB - 9)
    assert upload(h, just_right).status_code == 201
    too_big = b"%PDF-1.4\n" + b"1" * (5 * MB)
    assert upload(h, too_big).status_code == 413
    def stream():
        yield b"%PDF-1.4\n"
        for _ in range(6):
            yield b"2" * MB
    r = client.post("/api/documents", params={"doc_type": "other"}, content=stream(), headers=h)
    assert r.status_code == 413 and "5 MB" in r.json()["detail"]
    assert len(client.get("/api/documents", headers=h).json()["documents"]) == 1


def test_exact_duplicates_are_refused():
    h = farmer()
    data = pdf()
    assert upload(h, data).status_code == 201
    again = upload(h, data, doc_type="aadhaar")
    assert again.status_code == 409 and "already uploaded" in again.json()["detail"]
    assert upload(farmer(), data).status_code == 201


def test_per_farmer_limits_on_count_and_total_size(monkeypatch):
    h = farmer()
    monkeypatch.setattr(settings, "max_documents_per_user", 2)
    assert upload(h).status_code == 201 and upload(h).status_code == 201
    third = upload(h)
    assert third.status_code == 409 and "up to 2" in third.json()["detail"]
    monkeypatch.setattr(settings, "max_documents_per_user", 25)
    monkeypatch.setattr(settings, "max_storage_mb_per_user", 1)
    big = b"%PDF-1.4\n" + b"x" * (700 * 1024)
    h2 = farmer()
    assert upload(h2, big + b"a").status_code == 201
    over = upload(h2, big + b"b")
    assert over.status_code == 413 and "storage limit" in over.json()["detail"]


def test_uploads_are_rate_limited_per_farmer(monkeypatch):
    h = farmer()
    monkeypatch.setattr(upload_limiter, "max_failures", 3)
    for _ in range(3):
        assert upload(h).status_code == 201
    blocked = upload(h)
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers
    assert upload(farmer()).status_code == 201


@pytest.mark.parametrize("raw,expected", [
    ("../../etc/passwd", "passwd.pdf"),
    ("..\\..\\windows\\win.ini.exe", "win.ini.pdf"),
    ("नमस्ते खसरा.pdf", "नमस्ते खसरा.pdf"),
    ("a" * 300 + ".pdf", "a" * 80 + ".pdf"),
    ("bad<>:\"|?*name.pdf", "badname.pdf"),
    ("ctrl\x00\x07chars.pdf", "ctrlchars.pdf"),
    ("...", "document.pdf"),
    ("", "document.pdf"),
])
def test_file_names_are_cleaned(raw, expected):
    assert clean_filename(raw, "application/pdf") == expected


def test_files_are_stored_under_random_names_inside_the_upload_folder_only():
    h = farmer()
    data = pdf()
    r = upload(h, data, filename="../../outside.pdf")
    assert r.status_code == 201
    db = SessionLocal()
    try:
        row = db.query(Document).filter_by(id=r.json()["id"]).one()
        assert NAME_RE.match(row.stored_name) and "outside" not in row.stored_name
        path = get_storage().path_for(row.user_id, row.stored_name)
        assert path.read_bytes() == data
        assert settings.upload_path in path.parents and path.parent.name == str(row.user_id)
    finally:
        db.close()
    assert not list(Path(settings.upload_path).rglob("*.part"))
    assert not (Path(settings.upload_path).parent / "outside.pdf").exists()


@pytest.mark.parametrize("bad", ["../x.pdf", "a/b.pdf", "..\\x.pdf", "ABCDEF" * 5 + "ab.pdf", "x" * 32 + ".exe", "", "0" * 32 + ".pdf/../../x"])
def test_the_storage_layer_refuses_unsafe_names(bad, tmp_path):
    with pytest.raises(ValueError):
        LocalStorage(tmp_path).path_for(1, bad)


def test_the_storage_layer_writes_atomically_and_deletes_quietly(tmp_path):
    store = LocalStorage(tmp_path)
    name = store.save(7, b"%PDF-1.4 data", ".pdf")
    assert store.exists(7, name) and not list(tmp_path.rglob("*.part"))
    store.delete(7, name); store.delete(7, name); store.delete(7, "../nope")
    assert not store.exists(7, name)


def test_a_failed_database_save_leaves_no_file_behind(monkeypatch):
    h = farmer()
    from sqlalchemy.orm import Session
    def broken_commit(self):
        raise IntegrityError("insert", {}, Exception("boom"))
    before = len(list(Path(settings.upload_path).rglob("*.pdf")))
    monkeypatch.setattr(Session, "commit", broken_commit)
    r = upload(h)
    monkeypatch.undo()
    assert r.status_code == 409
    assert len(list(Path(settings.upload_path).rglob("*.pdf"))) == before


def test_download_returns_the_same_bytes_with_safe_headers():
    h = farmer()
    data = jpeg()
    doc = upload(h, data, doc_type="photo", filename="मेरी फोटो.jpg").json()
    inline = client.get(f"/api/documents/{doc['id']}/file", headers=h)
    assert inline.status_code == 200 and inline.content == data
    assert inline.headers["content-type"] == "image/jpeg"
    assert inline.headers["x-content-type-options"] == "nosniff"
    assert "no-store" in inline.headers["cache-control"] and inline.headers["x-frame-options"] == "DENY"
    assert inline.headers["content-disposition"].startswith("inline;") and "filename*=UTF-8''" in inline.headers["content-disposition"]
    attachment = client.get(f"/api/documents/{doc['id']}/file?download=1", headers=h)
    assert attachment.headers["content-disposition"].startswith("attachment;") and attachment.content == data
    assert [e["payload"] for e in audit(h, "document_downloaded")] == [{"doc_type": "photo"}]


def test_a_missing_file_on_disk_gives_a_clear_message():
    h = farmer()
    doc = upload(h).json()
    db = SessionLocal()
    try:
        row = db.query(Document).filter_by(id=doc["id"]).one()
        get_storage().path_for(row.user_id, row.stored_name).unlink()
    finally:
        db.close()
    r = client.get(f"/api/documents/{doc['id']}/file", headers=h)
    assert r.status_code == 404 and "missing" in r.json()["detail"]


def test_other_farmers_cannot_see_download_change_or_delete_a_document():
    owner, other = farmer(), farmer()
    doc = upload(owner, doc_type="aadhaar").json()
    url = f"/api/documents/{doc['id']}"
    assert client.get(url + "/file", headers=other).status_code == 404
    assert client.patch(url, json={"note": "mine now"}, headers=other).status_code == 404
    assert client.delete(url, headers=other).status_code == 404
    assert client.get("/api/documents", headers=other).json()["documents"] == []
    assert client.get(url + "/file", headers=owner).status_code == 200
    assert client.get("/api/documents/999999/file", headers=other).status_code == 404


def test_every_route_needs_a_signed_in_farmer():
    for method, url in [("get", "/api/documents"), ("get", "/api/documents/1/file"), ("patch", "/api/documents/1"),
                        ("delete", "/api/documents/1"), ("get", "/api/documents/checklist/PM-KISAN")]:
        kwargs = {"json": {}} if method == "patch" else {}
        assert getattr(client, method)(url, **kwargs).status_code in (401, 403), url


def test_type_and_note_can_be_changed_and_the_note_cleared():
    h = farmer()
    doc = upload(h, note="old", doc_type="other").json()
    changed = client.patch(f"/api/documents/{doc['id']}", json={"doc_type": "bank_passbook", "note": "SBI"}, headers=h).json()
    assert changed["docType"] == "bank_passbook" and changed["note"] == "SBI"
    assert client.patch(f"/api/documents/{doc['id']}", json={"note": None}, headers=h).json()["note"] is None
    assert client.patch(f"/api/documents/{doc['id']}", json={"doc_type": "nonsense"}, headers=h).status_code == 422


def test_deleting_removes_the_record_and_the_file_and_frees_space():
    h = farmer()
    doc = upload(h).json()
    db = SessionLocal()
    try:
        row = db.query(Document).filter_by(id=doc["id"]).one()
        path = get_storage().path_for(row.user_id, row.stored_name)
        assert path.exists()
    finally:
        db.close()
    assert client.delete(f"/api/documents/{doc['id']}", headers=h).json() == {"deleted": True}
    assert not path.exists()
    assert client.delete(f"/api/documents/{doc['id']}", headers=h).status_code == 404
    assert client.get("/api/documents", headers=h).json()["usage"] == {"count": 0, "bytes": 0}


def test_the_audit_trail_records_what_happened_but_not_file_names():
    h = farmer()
    doc = upload(h, doc_type="aadhaar", filename="secret-aadhaar-1234.pdf", note="private note").json()
    client.delete(f"/api/documents/{doc['id']}", headers=h)
    up = audit(h, "document_uploaded")[0]["payload"]
    assert up["doc_type"] == "aadhaar" and up["size_bytes"] == doc["sizeBytes"] and up["content_type"] == "application/pdf"
    assert audit(h, "document_deleted")[0]["payload"] == {"doc_type": "aadhaar"}
    everything = json.dumps(client.get("/api/audit?limit=200", headers=h).json())
    assert "secret-aadhaar" not in everything and "private note" not in everything


@pytest.mark.parametrize("name,expected", [
    ("Aadhaar", "aadhaar"), ("Aadhaar/identity proof", "aadhaar"), ("Identity proof", "identity_proof"), ("Government photo ID", "identity_proof"),
    ("Photo identity", "identity_proof"), ("Farmer/land/tenancy records, where applicable", "land_record"), ("Lease evidence", "land_record"),
    ("Certified land records/possession certificate", "land_record"), ("Bank details", "bank_passbook"), ("Bank account and IFSC details", "bank_passbook"),
    ("Passbook", "bank_passbook"), ("Photograph", "photo"), ("Passport photo", "photo"), ("Ration card", "ration_card"), ("Caste certificate", "caste_certificate"),
    ("Disability certificate", "disability_certificate"), ("Soil Health Card", "soil_health_card"), ("Age proof", "age_proof"), ("Haryana domicile certificate", "residence_proof"),
    ("Project estimates/DPR", "project_documents"), ("Cash invoice", "project_documents"), ("Undertaking", "other"), ("Member list", "other"), ("Mobile number", "other"),
])
def test_scheme_document_names_map_to_document_types(name, expected):
    assert suggest_type(name) == expected


def test_an_aadhaar_upload_also_satisfies_an_identity_proof_request():
    assert set(satisfying_types("identity_proof")) == {"identity_proof", "aadhaar"} and satisfying_types("land_record") == ["land_record"]


def test_the_checklist_shows_which_required_documents_are_uploaded():
    h = farmer()
    scheme = next(s for s in client.get("/api/schemes").json()
                  if any(suggest_type(d["name"]) in ("aadhaar", "identity_proof") for d in s["documents"]) and any(suggest_type(d["name"]) == "bank_passbook" for d in s["documents"]))
    code = scheme["schemeCode"]
    before = client.get(f"/api/documents/checklist/{code}", headers=h).json()
    assert len(before["items"]) == len(scheme["documents"]) and not any(i["uploaded"] for i in before["items"])
    doc = upload(h, doc_type="aadhaar").json()
    after = client.get(f"/api/documents/checklist/{code}", headers=h).json()
    ids = [i for i in after["items"] if i["suggestedType"] in ("aadhaar", "identity_proof")]
    assert ids and all(i["uploaded"] and i["documentIds"] == [doc["id"]] for i in ids)
    assert not any(i["uploaded"] for i in after["items"] if i["suggestedType"] == "bank_passbook")
    assert all(i["documentIds"] == [] for i in after["items"] if not i["matchable"])
    other_farmer = client.get(f"/api/documents/checklist/{code}", headers=farmer()).json()
    assert not any(i["uploaded"] for i in other_farmer["items"])


def test_the_checklist_for_an_unknown_scheme_is_not_found():
    assert client.get("/api/documents/checklist/NOPE-1", headers=farmer()).status_code == 404


def test_file_type_detection_by_content():
    assert sniff_type(pdf()) == "application/pdf" and sniff_type(jpeg()) == "image/jpeg" and sniff_type(png()) == "image/png"
    assert sniff_type(b"") is None and sniff_type(b"%PD") is None
