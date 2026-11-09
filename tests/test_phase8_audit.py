import uuid

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.evaluation import Evaluation
from app.services.application_status import APPLICATION_STATUSES
from app.services.audit import log_event
from app.services.scheme_service import get_scheme
from app.services.versioning import rule_fingerprint, scheme_version

client = TestClient(app)
PASSWORD = "StrongPass123"


def new_farmer():
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"name": "Test Farmer", "email": email, "password": PASSWORD}).json()
    return {"Authorization": f"Bearer {r['access_token']}"}, email


def trail(headers):
    return client.get("/api/audit", headers=headers).json()


def events(headers, name):
    return [e for e in trail(headers) if e["event"] == name]


# ---------- application statuses ----------

def test_exactly_the_seven_statuses_from_the_report_are_allowed():
    assert APPLICATION_STATUSES == ["Planning", "Documents Pending", "Applied", "Under Verification", "Approved", "Rejected", "Completed"]


def test_invalid_status_is_rejected_on_create_and_update():
    headers, _ = new_farmer()
    bad = client.post("/api/applications", json={"scheme_code": "PM-KISAN", "status": "Maybe later"}, headers=headers)
    assert bad.status_code == 422
    good = client.post("/api/applications", json={"scheme_code": "PM-KISAN", "status": "Applied"}, headers=headers)
    assert good.status_code == 200
    bad_update = client.put(f"/api/applications/{good.json()['id']}", json={"status": "Done!!"}, headers=headers)
    assert bad_update.status_code == 422


def test_every_allowed_status_can_be_set():
    headers, _ = new_farmer()
    app_id = client.post("/api/applications", json={"scheme_code": "PM-KISAN"}, headers=headers).json()["id"]
    for status in APPLICATION_STATUSES:
        r = client.put(f"/api/applications/{app_id}", json={"status": status}, headers=headers)
        assert r.status_code == 200 and r.json()["status"] == status


def test_planning_the_same_scheme_twice_updates_instead_of_duplicating():
    headers, _ = new_farmer()
    client.post("/api/applications", json={"scheme_code": "PM-KISAN", "status": "Planning"}, headers=headers)
    client.post("/api/applications", json={"scheme_code": "PM-KISAN", "status": "Documents Pending", "notes": "need land papers"}, headers=headers)
    rows = client.get("/api/applications", headers=headers).json()
    assert len(rows) == 1
    assert rows[0]["status"] == "Documents Pending" and rows[0]["notes"] == "need land papers"


def test_a_farmer_cannot_change_someone_elses_application():
    owner, _ = new_farmer()
    other, _ = new_farmer()
    app_id = client.post("/api/applications", json={"scheme_code": "PM-KISAN"}, headers=owner).json()["id"]
    assert client.put(f"/api/applications/{app_id}", json={"status": "Approved"}, headers=other).status_code == 404


# ---------- audit trail ----------

def test_register_login_and_failed_login_are_recorded_without_the_email():
    headers, email = new_farmer()
    client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
    client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    names = [e["event"] for e in trail(headers)]
    assert {"user_registered", "login_failed", "login_succeeded"} <= set(names)
    assert email not in str(trail(headers))


def test_profile_changes_store_field_names_never_values():
    headers, _ = new_farmer()
    client.post("/api/profile", json={"state": "Gujarat", "age": 41}, headers=headers)
    client.put("/api/profile", json={"state": "Gujarat", "age": 42, "farmer_type": "farmer"}, headers=headers)
    created = events(headers, "profile_created")[0]["payload"]["fields_changed"]
    updated = events(headers, "profile_updated")[0]["payload"]["fields_changed"]
    assert set(created) == {"state", "age"}
    assert set(updated) == {"age", "farmer_type"}
    assert "Gujarat" not in str(trail(headers))


def test_application_and_saved_scheme_actions_are_recorded():
    headers, _ = new_farmer()
    app_id = client.post("/api/applications", json={"scheme_code": "PM-KISAN"}, headers=headers).json()["id"]
    client.put(f"/api/applications/{app_id}", json={"status": "Applied"}, headers=headers)
    client.post("/api/saved-schemes", json={"scheme_code": "PMFBY"}, headers=headers)
    client.delete("/api/saved-schemes/PMFBY", headers=headers)
    assert events(headers, "application_created")[0]["payload"] == {"scheme_code": "PM-KISAN", "status": "Planning"}
    assert events(headers, "application_status_changed")[0]["payload"] == {"scheme_code": "PM-KISAN", "from": "Planning", "to": "Applied"}
    assert events(headers, "scheme_saved") and events(headers, "scheme_unsaved")


def test_each_farmer_sees_only_their_own_audit_trail():
    first, _ = new_farmer()
    second, _ = new_farmer()
    client.post("/api/saved-schemes", json={"scheme_code": "PMFBY"}, headers=first)
    assert events(second, "scheme_saved") == []
    assert client.get("/api/audit").status_code in (401, 403)


def test_audit_failure_never_breaks_the_request():
    class BrokenDb:
        def add(self, _): raise RuntimeError("database is down")
        def rollback(self): raise RuntimeError("cannot roll back")
    log_event(BrokenDb(), 1, "anything")  # must not raise


# ---------- versioning ----------

def test_rule_fingerprint_is_stable_and_changes_when_rules_change():
    scheme = get_scheme("AGR-50")
    assert rule_fingerprint(scheme) == rule_fingerprint(dict(scheme))
    assert len(rule_fingerprint(scheme)) == 12
    edited = dict(scheme, eligibility={"logic": "AND", "conditions": []})
    assert rule_fingerprint(edited) != rule_fingerprint(scheme)
    # texts that do not affect eligibility do not change the fingerprint
    assert rule_fingerprint(dict(scheme, description="new wording")) == rule_fingerprint(scheme)


def test_scheme_version_is_never_empty():
    assert scheme_version({"lastVerifiedAt": "2026-09-01"}) == "2026-09-01"
    assert scheme_version({}) == "unverified"


def test_evaluation_stores_and_returns_versions_and_logs_an_event():
    headers, _ = new_farmer()
    result = client.post("/api/eligibility/evaluate", json={"scheme_code": "AGR-50", "profile": {"state": "Gujarat", "farmer_type": "farmer"}}, headers=headers).json()
    assert result["ruleVersion"] == rule_fingerprint(get_scheme("AGR-50"))
    assert result["schemeVersion"]
    history = client.get("/api/eligibility/history", headers=headers).json()
    assert history[0]["ruleVersion"] == result["ruleVersion"] and history[0]["schemeVersion"] == result["schemeVersion"]
    logged = events(headers, "evaluation_run")[0]["payload"]
    assert logged["evaluation_id"] == result["evaluationId"] and logged["scheme_code"] == "AGR-50"


def test_old_evaluation_can_be_replayed_and_flags_changed_rules():
    headers, _ = new_farmer()
    result = client.post("/api/eligibility/evaluate", json={"scheme_code": "AGR-50", "profile": {"state": "Gujarat", "farmer_type": "farmer"}}, headers=headers).json()
    detail = client.get(f"/api/eligibility/history/{result['evaluationId']}", headers=headers).json()
    assert detail["profileSnapshot"]["state"] == "Gujarat"
    assert detail["criteria"] and detail["rulesChangedSince"] is False
    # pretend the scheme's rules were different when this evaluation was made
    db = SessionLocal()
    try:
        db.query(Evaluation).filter_by(id=result["evaluationId"]).update({"rule_version": "oldrules0000"})
        db.commit()
    finally:
        db.close()
    assert client.get(f"/api/eligibility/history/{result['evaluationId']}", headers=headers).json()["rulesChangedSince"] is True


def test_a_farmer_cannot_open_someone_elses_evaluation():
    owner, _ = new_farmer()
    other, _ = new_farmer()
    ev = client.post("/api/eligibility/evaluate", json={"scheme_code": "AGR-50", "profile": {"state": "Gujarat"}}, headers=owner).json()
    assert client.get(f"/api/eligibility/history/{ev['evaluationId']}", headers=other).status_code == 404
