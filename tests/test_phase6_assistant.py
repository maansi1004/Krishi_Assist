import uuid

from fastapi.testclient import TestClient

from app.api.assistant import find_scheme_for_question
from app.main import app
from app.services.scheme_service import load_schemes

client = TestClient(app)


def code(question, profile=None):
    scheme = find_scheme_for_question(question, profile or {})
    return scheme["schemeCode"] if scheme else None


def test_loose_letters_inside_other_words_do_not_match_a_scheme():
    assert code("how do I configure my account") is None
    assert code("what is the figure for rice yield") is None


def test_schemes_that_used_to_be_unreachable_are_found_by_name():
    assert code("Kisan credit card") == "KCC-MISS"
    assert code("tell me about pension") == "PM-KMY"
    assert code("solar pump") == "PM-KUSUM"
    assert code("bamboo") == "MIDH-NBM"
    assert code("beekeeping subsidy") == "NBHM"
    assert code("I want to know about the 6000 rupees") == "PM-KISAN"
    assert code("FIG scheme in Tamil Nadu") == "TN-FIG-001"
    assert code("कृषि प्रशिक्षण") == "GJ-AGRI-SKILL"


def test_loose_word_does_not_pick_a_scheme_from_another_state():
    # "irrigation" is a loose topic word; Har Khet Ko Pani is only for Uttarakhand.
    assert code("tell me about irrigation", {"state": "Punjab"}) != "UK-PMKSY-HKKP"
    assert code("tell me about irrigation", {"state": "Uttarakhand"}) == "UK-PMKSY-HKKP"


def test_real_scheme_name_wins_even_from_another_state():
    assert code("tell me about har khet ko pani", {"state": "Punjab"}) == "UK-PMKSY-HKKP"


def test_scheme_file_is_loaded_once_and_reused():
    assert load_schemes() is load_schemes()


def _signed_in_gujarat_farmer():
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    token = client.post("/api/auth/register", json={"name": "Test Farmer", "email": email, "password": "StrongPass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/profile", json={"farmer_type": "farmer", "state": "Gujarat"}, headers=headers)
    return headers


def test_eligibility_reply_uses_plain_sentences_not_field_names():
    headers = _signed_in_gujarat_farmer()
    reply = client.post("/api/assistant/chat", json={"message": "Am I eligible for tractor subsidy?", "language": "en"}, headers=headers).json()["reply"]
    assert "agr50_" not in reply
    assert "Pre-approval must be obtained" in reply


def test_eligibility_reply_follows_the_chosen_language():
    headers = _signed_in_gujarat_farmer()
    reply = client.post("/api/assistant/chat", json={"message": "Am I eligible for tractor subsidy?", "language": "hi"}, headers=headers).json()["reply"]
    assert "ज़रूरी जानकारी" in reply
    assert "Information needed" not in reply


def test_eligibility_reply_warns_when_scheme_data_is_unverified():
    headers = _signed_in_gujarat_farmer()
    data = client.post("/api/assistant/chat", json={"message": "Am I eligible for pension?", "language": "en"}, headers=headers).json()
    assert data["eligibility"]["status"] not in {"ELIGIBLE", "ALMOST_ELIGIBLE"}
    assert "still being verified" in data["reply"]


def test_eligibility_reply_has_no_double_full_stops():
    headers = _signed_in_gujarat_farmer()
    reply = client.post("/api/assistant/chat", json={"message": "Am I eligible for pension?", "language": "en"}, headers=headers).json()["reply"]
    assert ".." not in reply
