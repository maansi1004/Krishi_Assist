from fastapi.testclient import TestClient
from app.main import app


def test_root_health_and_scheme_data():
    c = TestClient(app)
    assert c.get("/").status_code == 200
    assert c.get("/health").status_code == 200
    r = c.get("/api/schemes")
    assert r.status_code == 200 and len(r.json()) >= 11


def test_only_authenticated_evaluation_route_is_registered():
    paths = [r.path for r in app.routes if r.path == "/api/eligibility/evaluate"]
    assert len(paths) == 1


def test_authenticated_report_endpoint():
    c = TestClient(app)
    email = "report-smoke@example.com"
    r = c.post("/api/auth/register", json={"name":"Report Farmer","email":email,"password":"StrongPass123"})
    if r.status_code == 409:
        r = c.post("/api/auth/login", json={"email":email,"password":"StrongPass123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = c.get("/api/reports/scheme/PM-KISAN", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/pdf")
