from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.auth.security import hash_password, verify_password, create_access_token
router=APIRouter(prefix="/api/auth",tags=["auth"])
@router.post("/register")
def register(req:RegisterRequest,db:Session=Depends(get_db)):
    if db.query(User).filter(User.email==req.email.lower()).first(): raise HTTPException(409,"Email already registered")
    u=User(name=req.name,email=req.email.lower(),password_hash=hash_password(req.password),role="farmer"); db.add(u); db.commit(); db.refresh(u)
    return {"access_token":create_access_token(u.id,u.role),"token_type":"bearer","user":{"id":u.id,"name":u.name,"email":u.email,"role":u.role}}
@router.post("/login")
def login(req:LoginRequest,db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==req.email.lower()).first()
    if not u or not verify_password(req.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"access_token":create_access_token(u.id,u.role),"token_type":"bearer","user":{"id":u.id,"name":u.name,"email":u.email,"role":u.role}}
