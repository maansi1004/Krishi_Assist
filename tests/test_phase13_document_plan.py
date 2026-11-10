import os
import uuid
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.document import DocumentChoice
from app.services.document_types import DOCUMENT_TYPES, suggest_type
from app.services.how_to_get import GUIDE, LINKS, how_to_get

client = TestClient(app)


def farmer():
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"name": "Test Farmer", "email": email, "password": "StrongPass123"}).json()
    return {"Authorization": f"Bearer {r['access_token']}"}


def upload(h, doc_type, tag=""):
    data = b"%PDF-1.4\n% " + (tag or uuid.uuid4().hex).encode() + b"\n"
    r = client.post("/api/documents", params={"doc_type": doc_type, "filename": "scan.pdf"}, content=data, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def my_id(h):
    return client.get("/api/profile", headers=h).json()["user_id"]


def plan(h, code):
    r = client.get(f"/api/documents/plan/{code}", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def choose(h, code, name, choice):
    return client.put(f"/api/documents/plan/{code}", json={"document_name": name, "choice": choice}, headers=h)


def scheme_with(*wanted):
    for s in client.get("/api/schemes").json():
        types = {suggest_type(d["name"]) for d in s["documents"]}
        if set(wanted) <= types:
            return s
    pytest.skip(f"no scheme with {wanted}")


def item(p, doc_type):
    return next(i for i in p["items"] if i["suggestedType"] == doc_type)


def names_of(s, doc_type):
    return [d["name"] for d in s["documents"] if suggest_type(d["name"]) == doc_type]


def test_a_new_farmer_has_not_answered_anything_and_gets_how_to_guidance_for_every_document():
    h = farmer()
    s = scheme_with("land_record", "bank_passbook")
    p = plan(h, s["schemeCode"])
    assert len(p["items"]) == len(s["documents"])
    assert {i["status"] for i in p["items"]} == {"undecided"} and p["nextSteps"] == []
    assert all(i["howToGet"] and i["howToGet"]["steps"]["en"] for i in p["items"])
    sm = p["summary"]
    assert sm["total"] == len(s["documents"]) and sm["undecided"] == sm["total"] and sm["ready"] == 0
    assert sm["required"] == sum(1 for d in s["documents"] if d["requiredType"] == "required")


def test_uploading_the_right_kind_of_document_makes_that_item_ready_and_deleting_it_undoes_that():
    h = farmer()
    s = scheme_with("land_record", "bank_passbook")
    code = s["schemeCode"]
    doc = upload(h, "land_record")
    p = plan(h, code)
    ready = [i for i in p["items"] if i["suggestedType"] == "land_record"]
    assert ready and all(i["status"] == "ready" and i["documentIds"] == [doc["id"]] and i["howToGet"] is None for i in ready)
    assert item(p, "bank_passbook")["status"] == "undecided"
    assert p["summary"]["ready"] == len(ready)
    client.delete(f"/api/documents/{doc['id']}", headers=h)
    assert item(plan(h, code), "land_record")["status"] == "undecided"


def test_i_dont_have_it_yet_creates_next_steps_in_all_three_languages():
    h = farmer()
    s = scheme_with("land_record", "bank_passbook")
    code, name = s["schemeCode"], names_of(s, "bank_passbook")[0]
    p = choose(h, code, name, "dont_have").json()
    steps = [n for n in p["nextSteps"] if n["name"] == name]
    assert len(steps) == 1 and steps[0]["suggestedType"] == "bank_passbook"
    how = steps[0]["howToGet"]
    assert set(how["steps"]) == {"en", "hi", "hinglish"} and all(len(v) >= 2 for v in how["steps"].values())
    assert set(how["title"]) == {"en", "hi", "hinglish"}
    assert item(p, "bank_passbook")["status"] == "to_arrange" and p["summary"]["toArrange"] >= 1


def test_not_applicable_closes_the_item_without_any_next_step():
    h = farmer()
    s = scheme_with("land_record", "bank_passbook")
    code, name = s["schemeCode"], names_of(s, "land_record")[0]
    before = plan(h, code)["summary"]
    p = choose(h, code, name, "not_applicable").json()
    assert next(i for i in p["items"] if i["name"] == name)["status"] == "not_applicable"
    assert p["nextSteps"] == [] and p["summary"]["notApplicable"] == 1 and p["summary"]["undecided"] == before["undecided"] - 1


def test_i_have_it_works_even_for_scheme_specific_documents_that_cannot_be_uploaded_as_a_known_type():
    h = farmer()
    s = next((s for s in client.get("/api/schemes").json() if any(suggest_type(d["name"]) == "other" for d in s["documents"])), None)
    assert s, "expected at least one scheme with a scheme-specific document"
    name = names_of(s, "other")[0]
    upload(h, "other")
    assert next(i for i in plan(h, s["schemeCode"])["items"] if i["name"] == name)["status"] == "undecided"
    p = choose(h, s["schemeCode"], name, "have_it").json()
    assert next(i for i in p["items"] if i["name"] == name)["status"] == "ready_self"
    assert p["summary"]["ready"] >= 1 and p["nextSteps"] == []


def test_an_answer_can_be_changed_and_cleared():
    h = farmer()
    s = scheme_with("land_record")
    code, name = s["schemeCode"], names_of(s, "land_record")[0]
    choose(h, code, name, "dont_have"); choose(h, code, name, "not_applicable")
    p = choose(h, code, name, None).json()
    assert next(i for i in p["items"] if i["name"] == name)["status"] == "undecided" and p["nextSteps"] == []
    db = SessionLocal()
    try:
        assert db.query(DocumentChoice).filter_by(user_id=my_id(h), scheme_code=code, document_name=name).count() == 0
    finally:
        db.close()


def test_changing_an_answer_updates_one_record_not_many():
    h = farmer()
    s = scheme_with("land_record")
    code, name = s["schemeCode"], names_of(s, "land_record")[0]
    for c in ("dont_have", "have_it", "dont_have"):
        choose(h, code, name, c)
    db = SessionLocal()
    try:
        assert db.query(DocumentChoice).filter_by(user_id=my_id(h), scheme_code=code, document_name=name).count() == 1
    finally:
        db.close()


def test_a_real_upload_beats_an_earlier_answer_and_the_answer_returns_if_the_file_is_deleted():
    h = farmer()
    s = scheme_with("bank_passbook")
    code, name = s["schemeCode"], names_of(s, "bank_passbook")[0]
    choose(h, code, name, "dont_have")
    doc = upload(h, "bank_passbook")
    p = plan(h, code)
    assert next(i for i in p["items"] if i["name"] == name)["status"] == "ready" and p["nextSteps"] == []
    client.delete(f"/api/documents/{doc['id']}", headers=h)
    assert next(i for i in plan(h, code)["items"] if i["name"] == name)["status"] == "to_arrange"


def test_an_aadhaar_upload_also_answers_a_request_for_identity_proof():
    h = farmer()
    s = scheme_with("identity_proof")
    upload(h, "aadhaar")
    assert item(plan(h, s["schemeCode"]), "identity_proof")["status"] == "ready"


def test_next_steps_list_required_documents_first():
    h = farmer()
    s = max(client.get("/api/schemes").json(), key=lambda s: len({d["requiredType"] for d in s["documents"]}))
    code = s["schemeCode"]
    for d in s["documents"]:
        choose(h, code, d["name"], "dont_have")
    order = {"required": 0, "conditional": 1, "verification": 2}
    ranks = [order.get(n["requiredType"], 3) for n in plan(h, code)["nextSteps"]]
    assert ranks == sorted(ranks) and len(ranks) == len(s["documents"])


def test_the_summary_numbers_always_add_up():
    h = farmer()
    s = max(client.get("/api/schemes").json(), key=lambda s: len(s["documents"]))
    code, docs = s["schemeCode"], s["documents"]
    for d, c in zip(docs, ["dont_have", "not_applicable", "have_it", None, "dont_have"]):
        choose(h, code, d["name"], c)
    sm = plan(h, code)["summary"]
    assert sm["ready"] + sm["notApplicable"] + sm["toArrange"] + sm["undecided"] == sm["total"] == len(docs)
    assert sm["requiredReady"] + sm["requiredOpen"] <= sm["required"]


def test_bad_requests_are_refused():
    h = farmer()
    s = scheme_with("land_record")
    code, name = s["schemeCode"], names_of(s, "land_record")[0]
    assert choose(h, code, "A document this scheme never asks for", "have_it").status_code == 422
    assert client.put(f"/api/documents/plan/{code}", json={"document_name": name, "choice": "maybe"}, headers=h).status_code == 422
    assert client.get("/api/documents/plan/NOPE-1", headers=h).status_code == 404
    assert choose(h, "NOPE-1", name, "have_it").status_code == 404
    assert client.get(f"/api/documents/plan/{code}").status_code in (401, 403)
    assert client.put(f"/api/documents/plan/{code}", json={"document_name": name, "choice": "have_it"}).status_code in (401, 403)


def test_one_farmers_answers_and_uploads_never_affect_another_farmer():
    mine, theirs = farmer(), farmer()
    s = scheme_with("land_record", "bank_passbook")
    code = s["schemeCode"]
    choose(mine, code, names_of(s, "bank_passbook")[0], "dont_have"); upload(mine, "land_record")
    other = plan(theirs, code)
    assert {i["status"] for i in other["items"]} == {"undecided"} and other["nextSteps"] == [] and other["summary"]["ready"] == 0


def test_answers_are_recorded_in_the_audit_trail_without_extra_detail():
    h = farmer()
    s = scheme_with("land_record")
    choose(h, s["schemeCode"], names_of(s, "land_record")[0], "not_applicable")
    events = [e for e in client.get("/api/audit?limit=100", headers=h).json() if e["event"] == "document_plan_updated"]
    assert events and events[0]["payload"] == {"scheme_code": s["schemeCode"], "choice": "not_applicable"}


def test_every_document_type_has_aligned_guidance_in_three_languages():
    for t in DOCUMENT_TYPES:
        g = how_to_get(t["id"])
        assert set(g["title"]) == {"en", "hi", "hinglish"} and all(g["title"].values()), t["id"]
        counts = {lang: len(steps) for lang, steps in g["steps"].items()}
        assert set(counts) == {"en", "hi", "hinglish"} and min(counts.values()) >= 2, t["id"]
        assert len(set(counts.values())) == 1, f"{t['id']}: the three languages must have the same number of steps {counts}"
        assert all(s.strip() for steps in g["steps"].values() for s in steps)


def test_only_known_official_websites_are_linked():
    allowed = {"uidai.gov.in", "www.digilocker.gov.in", "www.swavlambancard.gov.in", "soilhealth.dac.gov.in"}
    for key, link in LINKS.items():
        parsed = urlparse(link["url"])
        assert parsed.scheme == "https" and parsed.netloc in allowed, key
    assert all(set(g["links"]) <= set(LINKS) for g in GUIDE.values())
    assert how_to_get("not-a-type") == how_to_get("other")


def test_document_types_say_how_many_schemes_ask_for_them():
    types = client.get("/api/documents/types").json()
    total = len(client.get("/api/schemes").json())
    counts = {t["id"]: t["usedBySchemes"] for t in types}
    assert all(0 <= c <= total for c in counts.values()) and max(counts.values()) > 0
    assert counts["aadhaar"] >= counts["identity_proof"]
