from fastapi.testclient import TestClient
from app.main import app

def test_health(): assert TestClient(app).get("/health").status_code==200
def test_register_login_and_profile():
    c=TestClient(app); email="phase3@example.com"
    r=c.post("/api/auth/register",json={"name":"Test Farmer","email":email,"password":"StrongPass123"}); assert r.status_code==200
    token=r.json()["access_token"]; h={"Authorization":f"Bearer {token}"}
    profile={"farmer_name":"Test Farmer","farmer_type":"farmer","state":"Gujarat","extra_attributes":{}}
    r=c.post("/api/profile",json=profile,headers=h); assert r.status_code==200
    r=c.get("/api/profile",headers=h); assert r.status_code==200 and r.json()["profile"]["state"]=="Gujarat"
    r=c.post("/api/eligibility/evaluate",json={"scheme_code":"AGR-50","profile":profile},headers=h); assert r.status_code==200
    assert r.json()["status"] in {"ALMOST_ELIGIBLE","ELIGIBLE","VERIFICATION_REQUIRED"}
    r=c.get("/api/eligibility/history",headers=h); assert r.status_code==200 and len(r.json())>=1
