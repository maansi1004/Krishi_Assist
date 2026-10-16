from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import current_user
from app.db.session import get_db
from app.models.profile import FarmProfile
from app.models.user import User
from app.schemas.profile import FarmerProfile
router=APIRouter(prefix="/api/profile",tags=["profile"])
FIELDS=list(FarmerProfile.model_fields.keys())
def to_dict(p): return {f:getattr(p,f) for f in FIELDS}
@router.get("")
def get_profile(user:User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(FarmProfile).filter_by(user_id=user.id).first()
    return {"user_id":user.id,"profile":to_dict(p) if p else None}
@router.post("")
def create_profile(data:FarmerProfile,user:User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(FarmProfile).filter_by(user_id=user.id).first()
    if not p: p=FarmProfile(user_id=user.id); db.add(p)
    for f in FIELDS: setattr(p,f,getattr(data,f))
    db.commit(); db.refresh(p); return {"user_id":user.id,"profile":to_dict(p)}
@router.put("")
def update_profile(data:FarmerProfile,user:User=Depends(current_user),db:Session=Depends(get_db)):
    return create_profile(data,user,db)
