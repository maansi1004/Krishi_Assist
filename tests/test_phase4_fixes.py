import json
from pathlib import Path
from app.api.assistant import classify, find_scheme_for_question
from app.engines.eligibility_engine import evaluate_scheme
from app.services.scheme_service import load_schemes


def test_hindi_intent_and_scheme_resolution():
    assert classify("फसल बीमा के दस्तावेज क्या चाहिए") == "documents"
    s = find_scheme_for_question("ट्रैक्टर सब्सिडी", {"state": "Gujarat"})
    assert s and s["schemeCode"] == "AGR-50"


def test_general_agriculture_question_is_not_application_intent():
    assert classify("मिट्टी की जांच कैसे करें?") == "general_agriculture_support"


def test_translations_exist_for_all_active_schemes():
    for scheme in load_schemes():
        assert "hi" in scheme.get("translations", {})
        assert scheme["translations"]["hi"].get("name")
        assert scheme["translations"]["hi"].get("description")


def test_agr50_rule_engine_remains_authoritative():
    scheme = next(s for s in load_schemes() if s["schemeCode"] == "AGR-50")
    result = evaluate_scheme(scheme, {"state": "Punjab", "farmer_type": "farmer"})
    assert result["status"] == "NOT_ELIGIBLE"
