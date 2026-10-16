import json
from pathlib import Path

from app.schemas.scheme import Scheme


def test_all_scheme_json_parses_as_pydantic_models():
    path = Path(__file__).resolve().parents[1] / "data" / "schemes.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    models = [Scheme.model_validate(item) for item in data]
    assert len(models) == 11
    assert {m.schemeCode for m in models} == {item["schemeCode"] for item in data}
