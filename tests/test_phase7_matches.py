import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.services.profile_service import profile_completeness
from app.services.scheme_service import load_schemes

client = TestClient(app)

AGR50_ANSWERS = {
    "agr50_empanelled_tractor_model": True,
    "agr50_authorized_dealer": True,
    "agr50_preapproval": True,
    "tractor_pto_hp": 40,
    "tractor_eligible_expense": 200000,
}


def new_farmer(profile=None):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    token = client.post("/api/auth/register", json={"name": "Test Farmer", "email": email, "password": "StrongPass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    if profile is not None:
        assert client.post("/api/profile", json=profile, headers=headers).status_code in (200, 201)
    return headers


def codes(group):
    return [item["schemeCode"] for item in group]


def test_completeness_lists_what_is_missing():
    result = profile_completeness({"state": "Gujarat", "kcc_holder": False}, load_schemes())
    missing = [m["field"] for m in result["missing"]]
    assert "state" not in missing
    assert "kcc_holder" not in missing          # False is a real answer, not "missing"
    assert "age" in missing and "farmer_type" in missing
    assert result["complete"] is False
    assert result["filled"] + len(missing) == result["total"]


def test_completeness_treats_blank_text_as_missing():
    assert any(m["field"] == "state" for m in profile_completeness({"state": "  "}, load_schemes())["missing"])


def test_matches_need_sign_in():
    assert client.get("/api/matches").status_code in (401, 403)
    assert client.get("/api/matches/completeness").status_code in (401, 403)


def test_no_saved_profile_asks_for_profile_first():
    data = client.get("/api/matches", headers=new_farmer()).json()
    assert data["profileUsed"] is False
    assert data["profileCompleteness"]["complete"] is False
    assert all(items == [] for items in data["groups"].values())


def test_every_scheme_lands_in_exactly_one_group():
    data = client.get("/api/matches", headers=new_farmer({"farmer_type": "farmer", "state": "Gujarat"})).json()
    placed = [c for items in data["groups"].values() for c in codes(items)]
    assert len(placed) == len(set(placed)) == data["schemeCount"] == len(load_schemes())
    assert sum(data["counts"].values()) == data["schemeCount"]


def test_gujarat_farmer_sees_tractor_scheme_as_almost_eligible_with_questions():
    data = client.get("/api/matches", headers=new_farmer({"farmer_type": "farmer", "state": "Gujarat"})).json()
    almost = {i["schemeCode"]: i for i in data["groups"]["ALMOST_ELIGIBLE"]}
    assert "AGR-50" in almost
    assert almost["AGR-50"]["questionsToAnswer"] >= 1


def test_answering_the_questions_moves_the_scheme_to_eligible():
    profile = {"farmer_type": "farmer", "state": "Gujarat", "extra_attributes": AGR50_ANSWERS}
    data = client.get("/api/matches", headers=new_farmer(profile)).json()
    assert "AGR-50" in codes(data["groups"]["ELIGIBLE"])


def test_unverified_schemes_never_appear_as_eligible_or_almost():
    data = client.get("/api/matches", headers=new_farmer({"farmer_type": "farmer", "state": "Punjab", "age": 65})).json()
    shown = data["groups"]["ELIGIBLE"] + data["groups"]["ALMOST_ELIGIBLE"]
    assert not [i["schemeCode"] for i in shown if i["unverifiedScheme"]]


def test_farmers_own_state_comes_first_and_other_states_are_flagged():
    data = client.get("/api/matches", headers=new_farmer({"farmer_type": "farmer", "state": "Gujarat"})).json()
    almost = data["groups"]["ALMOST_ELIGIBLE"]
    assert almost[0]["state"] == "Gujarat"
    not_eligible = data["groups"]["NOT_ELIGIBLE"]
    assert not_eligible and all(i["otherState"] for i in not_eligible if i["state"] not in (None, "All India", "Gujarat"))
    assert all(i["reason"] for i in not_eligible)


def test_checking_all_schemes_does_not_fill_the_evaluation_history():
    headers = new_farmer({"farmer_type": "farmer", "state": "Gujarat"})
    client.get("/api/matches", headers=headers)
    assert client.get("/api/eligibility/history", headers=headers).json() == []


def test_completeness_endpoint_follows_the_saved_profile():
    headers = new_farmer({"state": "Gujarat"})
    before = client.get("/api/matches/completeness", headers=headers).json()
    client.put("/api/profile", json={"state": "Gujarat", "farmer_type": "farmer", "age": 40}, headers=headers)
    after = client.get("/api/matches/completeness", headers=headers).json()
    assert after["filled"] == before["filled"] + 2
