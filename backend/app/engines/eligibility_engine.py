from __future__ import annotations
from enum import Enum
from typing import Any


class Result(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


SUPPORTED_OPERATORS = {
    "equals", "not_equals", "gt", "gte", "lt", "lte", "in", "not_in", "exists"
}
SUPPORTED_LOGIC = {"AND", "OR", "NOT"}


def get_value(profile: dict[str, Any], field: str, source: str = "profile") -> Any:
    if source == "extra_attributes":
        return profile.get("extra_attributes", {}).get(field)
    return profile.get(field)


def compare(actual: Any, operator: str, expected: Any = None) -> Result:
    if operator not in SUPPORTED_OPERATORS:
        raise ValueError(f"Unsupported operator: {operator}")

    if operator == "exists":
        # False is a valid value; only None/missing means unknown.
        return Result.PASS if actual is not None else Result.UNKNOWN

    if actual is None:
        return Result.UNKNOWN

    try:
        if operator == "equals":
            return Result.PASS if actual == expected else Result.FAIL
        if operator == "not_equals":
            return Result.PASS if actual != expected else Result.FAIL
        if operator == "gt":
            return Result.PASS if actual > expected else Result.FAIL
        if operator == "gte":
            return Result.PASS if actual >= expected else Result.FAIL
        if operator == "lt":
            return Result.PASS if actual < expected else Result.FAIL
        if operator == "lte":
            return Result.PASS if actual <= expected else Result.FAIL
        if operator == "in":
            return Result.PASS if actual in expected else Result.FAIL
        if operator == "not_in":
            return Result.PASS if actual not in expected else Result.FAIL
    except (TypeError, ValueError):
        return Result.UNKNOWN

    raise ValueError(f"Unsupported operator: {operator}")


def _validate_rule_shape(rule: dict[str, Any]) -> None:
    if not isinstance(rule, dict):
        raise ValueError("Rule must be an object")

    logic = rule.get("logic")
    if logic is not None:
        if logic not in SUPPORTED_LOGIC:
            raise ValueError(f"Unsupported logic: {logic}")
        conditions = rule.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            raise ValueError(f"{logic} requires a non-empty conditions list")
        if logic == "NOT" and len(conditions) != 1:
            raise ValueError("NOT requires exactly one condition")
        for child in conditions:
            _validate_rule_shape(child)
        return

    if "fieldName" not in rule or "operator" not in rule:
        raise ValueError("Criterion requires fieldName and operator")
    if rule["operator"] not in SUPPORTED_OPERATORS:
        raise ValueError(f"Unsupported operator: {rule['operator']}")
    if rule.get("fieldSource", "profile") not in {"profile", "extra_attributes"}:
        raise ValueError("fieldSource must be profile or extra_attributes")


def _combine(logic: str, states: list[Result]) -> Result:
    if logic == "AND":
        if Result.FAIL in states:
            return Result.FAIL
        if Result.UNKNOWN in states:
            return Result.UNKNOWN
        return Result.PASS

    if logic == "OR":
        if Result.PASS in states:
            return Result.PASS
        if Result.UNKNOWN in states:
            return Result.UNKNOWN
        return Result.FAIL

    if logic == "NOT":
        return {Result.PASS: Result.FAIL, Result.FAIL: Result.PASS, Result.UNKNOWN: Result.UNKNOWN}[states[0]]

    raise ValueError(f"Unsupported logic: {logic}")


def evaluate_rule(rule: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    _validate_rule_shape(rule)
    logic = rule.get("logic")

    if logic:
        children = [evaluate_rule(child, profile) for child in rule["conditions"]]
        result = _combine(logic, [Result(child["result"]) for child in children])
        return {
            "type": "group",
            "logic": logic,
            "result": result.value,
            "children": children,
        }

    field = rule["fieldName"]
    source = rule.get("fieldSource", "profile")
    actual = get_value(profile, field, source)
    operator = rule["operator"]
    expected = rule.get("expectedValue")
    result = compare(actual, operator, expected)

    default_explanation = {
        Result.PASS: f"The provided value satisfies the requirement ({actual!r}).",
        Result.FAIL: f"The provided value ({actual!r}) does not satisfy the requirement ({expected!r}).",
        Result.UNKNOWN: "This requirement cannot be determined from the available profile information.",
    }[result]

    return {
        "type": "criterion",
        "field": field,
        "source": source,
        "operator": operator,
        "expected": expected,
        "actual": actual,
        "result": result.value,
        "criterion": rule.get("criterion", field.replace("_", " ").title()),
        "explanation": rule.get("explanation") or default_explanation,
        "remediation": rule.get("remediation"),
    }


def flatten_criteria(node: dict[str, Any]) -> list[dict[str, Any]]:
    if node["type"] == "criterion":
        return [node]
    result: list[dict[str, Any]] = []
    for child in node.get("children", []):
        result.extend(flatten_criteria(child))
    return result


def _evaluate_condition_list(conditions: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [evaluate_rule(condition, profile) for condition in conditions]


def calculate_benefits(scheme: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Calculate only explicitly machine-readable benefits.

    Descriptive benefits are returned as-is. Percentage/cap benefits require
    the declared basis field; missing basis means UNKNOWN rather than an invented amount.
    """
    results: list[dict[str, Any]] = []
    for benefit in scheme.get("benefitLimits", []):
        condition_result = Result.PASS
        condition_tree = None
        if benefit.get("condition"):
            condition_tree = evaluate_rule(benefit["condition"], profile)
            condition_result = Result(condition_tree["result"])

        base = {
            "benefitType": benefit.get("benefitType"),
            "description": benefit.get("description"),
            "basis": benefit.get("basis"),
            "result": condition_result.value,
        }
        if condition_tree:
            base["condition"] = condition_tree

        if condition_result != Result.PASS:
            results.append(base)
            continue

        if benefit["benefitType"] == "fixed_amount":
            base["amount"] = benefit.get("fixedAmount")
            base["calculation"] = "fixed_amount"
        elif benefit["benefitType"] == "percentage_or_cap":
            field = benefit.get("basisField")
            actual = get_value(profile, field, "extra_attributes") if field else None
            if actual is None:
                base["result"] = Result.UNKNOWN.value
                base["missingField"] = field
                base["calculation"] = "25% of eligible expense, capped at the stated maximum"
            else:
                percentage = benefit.get("percentage")
                maximum = benefit.get("maximumAmount")
                calculated = actual * percentage / 100
                base["basisAmount"] = actual
                base["percentage"] = percentage
                base["maximumAmount"] = maximum
                base["calculatedAmount"] = min(calculated, maximum)
                base["calculation"] = f"min({percentage}% × {actual}, {maximum})"
        else:
            base["calculation"] = "descriptive_only"

        results.append(base)
    return results


def evaluate_scheme(scheme: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    eligibility_tree = evaluate_rule(scheme["eligibility"], profile)
    exclusion_tree = evaluate_rule(scheme["exclusions"], profile) if scheme.get("exclusions") else None
    verification_trees = _evaluate_condition_list(scheme.get("verificationConditions", []), profile)

    criteria = flatten_criteria(eligibility_tree)
    exclusions = flatten_criteria(exclusion_tree) if exclusion_tree else []
    verification = [c for tree in verification_trees for c in flatten_criteria(tree)]

    eligibility_result = Result(eligibility_tree["result"])
    exclusion_result = Result(exclusion_tree["result"]) if exclusion_tree else Result.FAIL
    verification_result = (
        Result.FAIL if any(t["result"] == Result.FAIL.value for t in verification_trees)
        else Result.UNKNOWN if any(t["result"] == Result.UNKNOWN.value for t in verification_trees)
        else Result.PASS
    )

    # Exclusion PASS is a blocking rule. Exclusion UNKNOWN is unsafe to treat as pass.
    if exclusion_result == Result.PASS:
        status = "NOT_ELIGIBLE"
    elif eligibility_result == Result.FAIL:
        status = "NOT_ELIGIBLE"
    elif exclusion_result == Result.UNKNOWN:
        status = "VERIFICATION_REQUIRED"
    elif verification_result == Result.FAIL:
        status = "NOT_ELIGIBLE"
    elif eligibility_result == Result.UNKNOWN or verification_result == Result.UNKNOWN:
        status = "ALMOST_ELIGIBLE"
    else:
        status = "ELIGIBLE"

    missing = [c["field"] for c in criteria if c["result"] == Result.UNKNOWN.value]
    failed = [c["field"] for c in criteria if c["result"] == Result.FAIL.value]
    verification_required = [c["field"] for c in exclusions if c["result"] == Result.UNKNOWN.value]
    verification_required += [c["field"] for c in verification if c["result"] == Result.UNKNOWN.value]
    verification_failed = [c["field"] for c in verification if c["result"] == Result.FAIL.value]

    remediation = []
    for criterion in criteria + verification:
        if criterion.get("remediation") and criterion["result"] != Result.PASS.value:
            remediation.append(criterion["remediation"])

    # Deduplicate while preserving order.
    remediation = list(dict.fromkeys(remediation))
    missing = list(dict.fromkeys(missing))
    verification_required = list(dict.fromkeys(verification_required))

    return {
        "schemeCode": scheme["schemeCode"],
        "status": status,
        "criteria": criteria,
        "exclusions": exclusions,
        "verificationCriteria": verification,
        "missingRequirements": missing,
        "failedRequirements": failed + verification_failed,
        "remediation": remediation,
        "verificationRequired": verification_required,
        "benefits": scheme.get("benefits", []),
        "benefitCalculations": calculate_benefits(scheme, profile),
        "documents": scheme.get("documents", []),
        "actionPlan": scheme.get("actionSteps", []),
        "officialPortals": scheme.get("officialPortals", []),
        "sources": scheme.get("sources", []),
    }
