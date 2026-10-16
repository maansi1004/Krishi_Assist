from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencies import current_user
from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.models.profile import FarmProfile
from app.models.user import User
from app.schemas.eligibility import EligibilityRequest
from app.services.scheme_service import get_scheme
from app.engines.eligibility_engine import evaluate_scheme
router=APIRouter(prefix="/api/eligibility",tags=["eligibility"])
@router.post("/evaluate")
def evaluate(request:EligibilityRequest,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scheme=get_scheme(request.scheme_code)
    if not scheme: raise HTTPException(404,"Scheme not found")
    profile=request.profile.model_dump()
    result=evaluate_scheme(scheme,profile)
    ev=Evaluation(user_id=user.id,scheme_code=request.scheme_code,scheme_version=scheme.get("lastVerifiedAt"),overall_result=result["status"],profile_snapshot=profile,criterion_results=result["criteria"],missing_fields=result["missingRequirements"],remediation_steps=result["remediation"])
    db.add(ev); db.commit(); db.refresh(ev); result["evaluationId"]=ev.id; return result
@router.get("/history")
def history(user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Evaluation).filter_by(user_id=user.id).order_by(Evaluation.created_at.desc()).all()
    return [{"id":r.id,"schemeCode":r.scheme_code,"status":r.overall_result,"createdAt":r.created_at,"missingRequirements":r.missing_fields} for r in rows]
