import json
from pathlib import Path

import pytest

from app.engines.eligibility_engine import Result, evaluate_rule, evaluate_scheme, calculate_benefits
from app.services.scheme_validator import validate_schemes

DATA = Path(__file__).resolve().parents[1] / "data" / "schemes.json"


def schemes():
    return {s["schemeCode"]: s for s in json.loads(DATA.read_text(encoding="utf-8"))}


def test_all_schemes_validate():
    assert validate_schemes() == []


def test_all_11_reviewed_schemes_exist():
    expected = {
        "PM-KISAN", "PMFBY", "NFSM", "UK-PMKSY-HKKP", "UK-CAP-AROMATIC",
        "TN-FIG-001", "AS-MMKSSY", "AGR-2", "UK-AGRI-INV-CROP-LOSS",
        "AGR-50", "GJ-AGRI-SKILL"
    }
    assert expected.issubset(schemes())


def test_not_operator():
    rule = {"logic": "NOT", "conditions": [{"fieldName": "state", "operator": "equals", "expectedValue": "Gujarat"}]}
    assert evaluate_rule(rule, {"state": "Punjab"})["result"] == Result.PASS.value
    assert evaluate_rule(rule, {"state": "Gujarat"})["result"] == Result.FAIL.value
    assert evaluate_rule(rule, {})["result"] == Result.UNKNOWN.value


def test_nested_and_or_unknown_semantics():
    rule = {
        "logic": "AND",
        "conditions": [
            {"fieldName": "state", "operator": "equals", "expectedValue": "Gujarat"},
            {"logic": "OR", "conditions": [
                {"fieldName": "crop", "operator": "equals", "expectedValue": "wheat"},
                {"fieldName": "crop", "operator": "equals", "expectedValue": "rice"}
            ]}
        ]
    }
    assert evaluate_rule(rule, {"state": "Gujarat"})["result"] == Result.UNKNOWN.value
    assert evaluate_rule(rule, {"state": "Punjab", "crop": "wheat"})["result"] == Result.FAIL.value


def test_agr50_eligible_when_verifications_are_known():
    scheme = schemes()["AGR-50"]
    profile = {
        "state": "Gujarat", "farmer_type": "farmer",
        "extra_attributes": {
            "agr50_empanelled_tractor_model": True,
            "agr50_authorized_dealer": True,
            "agr50_preapproval": True,
            "tractor_pto_hp": 40,
            "tractor_eligible_expense": 200000,
        }
    }
    result = evaluate_scheme(scheme, profile)
    assert result["status"] == "ELIGIBLE"
    assert result["benefitCalculations"][0]["calculatedAmount"] == 45000


def test_agr50_almost_eligible_when_preapproval_unknown():
    scheme = schemes()["AGR-50"]
    profile = {
        "state": "Gujarat", "farmer_type": "farmer",
        "extra_attributes": {
            "agr50_empanelled_tractor_model": True,
            "agr50_authorized_dealer": True
        }
    }
    result = evaluate_scheme(scheme, profile)
    assert result["status"] == "ALMOST_ELIGIBLE"
    assert "agr50_preapproval" in result["verificationRequired"]


def test_agr50_state_failure_is_not_eligible():
    scheme = schemes()["AGR-50"]
    profile = {"state": "Punjab", "farmer_type": "farmer"}
    result = evaluate_scheme(scheme, profile)
    assert result["status"] == "NOT_ELIGIBLE"
    assert "state" in result["failedRequirements"]


def test_pmkisan_unknown_exclusion_is_not_ignored():
    scheme = schemes()["PM-KISAN"]
    profile = {"farmer_type": "farmer", "land_size_hectares": 2}
    result = evaluate_scheme(scheme, profile)
    assert result["status"] == "VERIFICATION_REQUIRED"
    assert result["verificationRequired"]


def test_pmkisan_exclusion_blocks():
    scheme = schemes()["PM-KISAN"]
    profile = {
        "farmer_type": "farmer", "land_size_hectares": 2,
        "extra_attributes": {"pmkisan_income_tax_payer": True}
    }
    result = evaluate_scheme(scheme, profile)
    assert result["status"] == "NOT_ELIGIBLE"


def test_uttarakhand_collective_rule_requires_both_extra_conditions():
    scheme = schemes()["UK-PMKSY-HKKP"]
    base = {"state": "Uttarakhand", "farmer_type": "farmer"}
    result = evaluate_scheme(scheme, {**base, "extra_attributes": {"project_type": "collective_irrigation", "command_area_hectares": 5, "groundwater_category": "safe"}})
    assert result["status"] == "ELIGIBLE"


def test_uttarakhand_individual_project_does_not_require_collective_criteria():
    scheme = schemes()["UK-PMKSY-HKKP"]
    result = evaluate_scheme(scheme, {"state": "Uttarakhand", "farmer_type": "farmer", "extra_attributes": {"project_type": "individual_groundwater_irrigation"}})
    assert result["status"] == "ELIGIBLE"


def test_benefit_missing_basis_is_unknown_not_zero():
    scheme = schemes()["AGR-50"]
    result = calculate_benefits(scheme, {"extra_attributes": {"tractor_pto_hp": 40}})
    assert result[0]["result"] == "UNKNOWN"
    assert result[0]["missingField"] == "tractor_eligible_expense"
