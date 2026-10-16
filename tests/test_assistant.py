from app.api.assistant import classify, score_scheme


def test_classify_documents():
    assert classify("what documents do I need for crop insurance") == "documents"


def test_classify_eligibility():
    assert classify("am I eligible for tractor subsidy") == "eligibility"


def test_context_score_prefers_state_and_need():
    scheme = {"category": "farm_mechanization", "description": "tractor assistance", "name": "AGR-50", "state": "Gujarat"}
    profile = {"state": "Gujarat", "primary_crop": "wheat"}
    assert score_scheme(scheme, "tractor subsidy", profile) > 50
