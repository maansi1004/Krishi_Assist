from fastapi import APIRouter, HTTPException
from app.schemas.eligibility import EligibilityRequest
from app.services.scheme_service import get_scheme
from app.engines.eligibility_engine import evaluate_scheme

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])


@router.post("/evaluate")
def evaluate(request: EligibilityRequest):
    scheme = get_scheme(request.scheme_code)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return evaluate_scheme(scheme, request.profile.model_dump())
