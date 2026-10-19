from app.engines.eligibility_engine import compare, evaluate_scheme, Result
from app.services.scheme_service import get_scheme, load_schemes


def test_text_matching_ignores_case_spaces_and_underscores():
    assert compare("gujarat ", "equals", "Gujarat") == Result.PASS
    assert compare("Tenant Farmer", "in", ["farmer", "tenant_farmer"]) == Result.PASS
    assert compare("PUNJAB", "equals", "Gujarat") == Result.FAIL
    assert compare("sc", "not_in", ["SC", "ST"]) == Result.FAIL


def test_blank_text_counts_as_unknown_not_fail():
    assert compare("", "equals", "Gujarat") == Result.UNKNOWN
    assert compare("   ", "exists") == Result.UNKNOWN


def test_numbers_and_booleans_still_work():
    assert compare(5, "gte", 5) == Result.PASS
    assert compare(False, "equals", True) == Result.FAIL
    assert compare(True, "equals", True) == Result.PASS


def test_agr50_accepts_lowercase_state_from_old_profiles():
    scheme = get_scheme("AGR-50")
    assert evaluate_scheme(scheme, {"state": "gujarat", "farmer_type": "Farmer"})["status"] != "NOT_ELIGIBLE"


def test_unverified_schemes_never_say_eligible():
    profile = {"farmer_type": "farmer", "state": "Punjab", "age": 65}
    for scheme in load_schemes():
        if scheme.get("status") == "verification_required":
            assert evaluate_scheme(scheme, profile)["status"] not in {"ELIGIBLE", "ALMOST_ELIGIBLE"}
