from app.engines.eligibility_engine import evaluate_rule, Result


def test_equals_pass():
    assert evaluate_rule({"fieldName":"state","operator":"equals","expectedValue":"Gujarat"}, {"state":"Gujarat"})["result"] == Result.PASS.value


def test_equals_fail():
    assert evaluate_rule({"fieldName":"state","operator":"equals","expectedValue":"Gujarat"}, {"state":"Punjab"})["result"] == Result.FAIL.value


def test_missing_is_unknown():
    assert evaluate_rule({"fieldName":"state","operator":"equals","expectedValue":"Gujarat"}, {})["result"] == Result.UNKNOWN.value


def test_nested_or():
    rule = {"logic":"OR","conditions":[{"fieldName":"state","operator":"equals","expectedValue":"Gujarat"},{"fieldName":"state","operator":"equals","expectedValue":"Punjab"}]}
    assert evaluate_rule(rule, {"state":"Punjab"})["result"] == Result.PASS.value
