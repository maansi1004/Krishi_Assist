import hashlib
import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.scripts.make_admin import main as make_admin_main, set_role
from app.services.scheme_admin import refresh_overrides
from app.services.scheme_service import DATA_FILE, set_overrides

client = TestClient(app)
PASSWORD = "StrongPass123"
REAL_RULES = "MH-NDKSP-001"     # reviewed rules, but still marked verification_required in the file
SINGLE_RULE = "PM-KMY"          # only one eligibility rule
TODAY = date.today().isoformat()


def register():
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    token = client.post("/api/auth/register", json={"name": "Test User", "email": email, "password": PASSWORD}).json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


def admin():
    email, headers = register()
    db = SessionLocal()
    try:
        assert set_role(db, email, "admin")
    finally:
        db.close()
    return headers


def codes_visible_to_farmers():
    return {s["schemeCode"] for s in client.get("/api/schemes").json()}


# ---------- who may use the admin side ----------

def test_only_admins_can_use_admin_endpoints():
    _, farmer = register()
    calls = [("get", "/api/admin/schemes", None), ("get", "/api/admin/coverage", None), ("get", "/api/admin/audit", None),
             ("put", f"/api/admin/schemes/{REAL_RULES}", {"status": "inactive"}),
             ("delete", f"/api/admin/schemes/{REAL_RULES}/override", None),
             ("post", "/api/admin/schemes/validate", {"scheme": {}})]
    for method, url, body in calls:
        kwargs = {"json": body} if body is not None else {}
        assert getattr(client, method)(url, headers=farmer, **kwargs).status_code == 403, url
        assert getattr(client, method)(url, **kwargs).status_code in (401, 403), url


def test_admin_rights_come_from_the_database_and_can_be_taken_away():
    email, headers = register()
    db = SessionLocal()
    try:
        set_role(db, email, "admin")
        assert client.get("/api/admin/coverage", headers=headers).status_code == 200
        set_role(db, email, "farmer")
        assert client.get("/api/admin/coverage", headers=headers).status_code == 403    # same token, rights gone
    finally:
        db.close()


def test_make_admin_script_handles_unknown_and_known_accounts():
    assert make_admin_main(["nobody-here@example.com"]) == 1
    assert make_admin_main([]) == 2
    email, headers = register()
    assert make_admin_main([email]) == 0
    assert client.get("/api/admin/coverage", headers=headers).status_code == 200
    assert make_admin_main([email, "--revoke"]) == 0
    assert client.get("/api/admin/coverage", headers=headers).status_code == 403


# ---------- listing and switching schemes ----------

def test_admin_sees_every_scheme_with_its_review_details():
    rows = client.get("/api/admin/schemes", headers=admin()).json()
    assert len(rows) == len(client.get("/api/schemes").json())
    row = next(r for r in rows if r["schemeCode"] == REAL_RULES)
    assert row["fileStatus"] == "verification_required" and row["overridden"] is False
    assert row["criteriaCount"] > 1 and row["sourceCount"] >= 1


def test_switching_a_scheme_off_hides_it_from_farmers_everywhere():
    headers = admin()
    before = len(client.get("/api/schemes").json())
    assert client.put("/api/admin/schemes/AGR-50", json={"status": "inactive"}, headers=headers).status_code == 200
    assert "AGR-50" not in codes_visible_to_farmers() and len(client.get("/api/schemes").json()) == before - 1
    assert client.get("/api/schemes/AGR-50").status_code == 404
    _, farmer = register()
    assert client.post("/api/eligibility/evaluate", json={"scheme_code": "AGR-50", "profile": {"state": "Gujarat"}}, headers=farmer).status_code == 404
    client.post("/api/profile", json={"state": "Gujarat", "farmer_type": "farmer"}, headers=farmer)
    matches = client.get("/api/matches", headers=farmer).json()
    assert matches["schemeCount"] == before - 1
    assert "AGR-50" not in {i["schemeCode"] for items in matches["groups"].values() for i in items}
    row = next(r for r in client.get("/api/admin/schemes", headers=headers).json() if r["schemeCode"] == "AGR-50")
    assert row["status"] == "inactive" and row["fileStatus"] == "active" and row["overridden"] is True


def test_marking_a_reviewed_scheme_verified_lifts_the_unverified_cap_and_sets_its_version():
    headers = admin()
    _, farmer = register()
    ask = {"scheme_code": REAL_RULES, "profile": {"state": "Maharashtra", "farmer_type": "farmer"}}
    assert client.post("/api/eligibility/evaluate", json=ask, headers=farmer).json()["unverifiedScheme"] is True
    updated = client.put(f"/api/admin/schemes/{REAL_RULES}", json={"status": "active"}, headers=headers).json()
    assert updated["status"] == "active" and updated["lastVerifiedAt"] == TODAY and updated["overridden"] is True
    result = client.post("/api/eligibility/evaluate", json=ask, headers=farmer).json()
    assert result["unverifiedScheme"] is False and result["schemeVersion"] == TODAY


def test_a_scheme_with_one_rule_needs_an_explicit_confirmation_to_switch_on():
    headers = admin()
    blocked = client.put(f"/api/admin/schemes/{SINGLE_RULE}", json={"status": "active"}, headers=headers)
    assert blocked.status_code == 409 and "only one eligibility rule" in blocked.json()["detail"]
    ok = client.put(f"/api/admin/schemes/{SINGLE_RULE}", json={"status": "active", "acknowledge_single_rule": True}, headers=headers)
    assert ok.status_code == 200 and ok.json()["status"] == "active"


def test_bad_requests_are_refused():
    headers = admin()
    future = (date.today() + timedelta(days=3)).isoformat()
    assert client.put(f"/api/admin/schemes/{REAL_RULES}", json={"status": "active", "last_verified_at": future}, headers=headers).status_code == 422
    assert client.put(f"/api/admin/schemes/{REAL_RULES}", json={"status": "deleted"}, headers=headers).status_code == 422
    assert client.put("/api/admin/schemes/NOPE-999", json={"status": "inactive"}, headers=headers).status_code == 404
    assert client.delete(f"/api/admin/schemes/{REAL_RULES}/override", headers=headers).status_code == 404


def test_removing_the_override_restores_exactly_what_the_file_says():
    headers = admin()
    client.put(f"/api/admin/schemes/{REAL_RULES}", json={"status": "active", "last_verified_at": "2026-01-05"}, headers=headers)
    restored = client.delete(f"/api/admin/schemes/{REAL_RULES}/override", headers=headers).json()
    assert restored["status"] == "verification_required" and restored["overridden"] is False and restored["lastVerifiedAt"] is None


def test_decisions_survive_a_server_restart_and_never_rewrite_the_scheme_file():
    before = hashlib.sha256(DATA_FILE.read_bytes()).hexdigest()
    headers = admin()
    client.put("/api/admin/schemes/AGR-50", json={"status": "inactive"}, headers=headers)
    set_overrides({})                      # what a restart does: memory is empty...
    assert "AGR-50" in codes_visible_to_farmers()
    db = SessionLocal()
    try:
        refresh_overrides(db)              # ...and the decisions are read back from the database
    finally:
        db.close()
    assert "AGR-50" not in codes_visible_to_farmers()
    assert hashlib.sha256(DATA_FILE.read_bytes()).hexdigest() == before


def test_admin_changes_are_audited_and_the_admin_log_shows_no_personal_details():
    email, headers = register()
    db = SessionLocal()
    try:
        set_role(db, email, "admin")
    finally:
        db.close()
    client.put(f"/api/admin/schemes/{REAL_RULES}", json={"status": "active", "last_verified_at": "2026-01-05"}, headers=headers)
    log = client.get("/api/admin/audit", headers=headers).json()
    event = next(e for e in log if e["event"] == "admin_scheme_updated")
    assert event["payload"] == {"scheme_code": REAL_RULES, "from_status": "verification_required", "to_status": "active", "last_verified_at": "2026-01-05"}
    assert email not in str(log)


# ---------- coverage report ----------

def test_coverage_report_counts_gaps_and_usage():
    headers = admin()
    report = client.get("/api/admin/coverage", headers=headers).json()
    total = report["totals"]["schemes"]
    assert total == report["totals"]["active"] + report["totals"]["verification_required"] + report["totals"].get("inactive", 0)
    assert sum(v["total"] for v in report["byState"].values()) == total
    assert set(report["gaps"]) == {"neverVerified", "staleVerification", "noSourceUrl", "hindiMissing", "singleRuleOnly"}
    assert "Gujarat" not in report["statesWithoutSchemes"] and "Punjab" in report["statesWithoutSchemes"]
    assert report["usage"]["farmers"] >= 0 and "evaluations" in report["usage"]
    client.put("/api/admin/schemes/AGR-50", json={"status": "inactive"}, headers=headers)
    assert client.get("/api/admin/coverage", headers=headers).json()["totals"]["inactive"] == 1


def test_stale_verification_dates_are_flagged():
    headers = admin()
    client.put(f"/api/admin/schemes/{REAL_RULES}", json={"status": "active", "last_verified_at": "2020-01-01"}, headers=headers)
    gaps = client.get("/api/admin/coverage", headers=headers).json()["gaps"]
    assert REAL_RULES in gaps["staleVerification"] and REAL_RULES not in gaps["neverVerified"]


# ---------- checking a new scheme file ----------

def test_validate_accepts_a_good_scheme_and_explains_a_bad_one():
    headers = admin()
    good = next(s for s in client.get("/api/schemes").json() if s["schemeCode"] == "AGR-50")
    result = client.post("/api/admin/schemes/validate", json={"scheme": {**good, "schemeCode": "NEW-TEST-001"}}, headers=headers).json()
    assert result["valid"] is True and result["errors"] == []
    clash = client.post("/api/admin/schemes/validate", json={"scheme": good}, headers=headers).json()
    assert clash["valid"] is True and any("already exists" in w for w in clash["warnings"])
    bad = client.post("/api/admin/schemes/validate", json={"scheme": {"schemeCode": "X"}}, headers=headers).json()
    assert bad["valid"] is False and bad["errors"]
