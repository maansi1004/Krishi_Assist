from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password, create_access_token, dummy_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.audit import log_event
from app.services.rate_limit import login_limiter, ip_limiter, register_limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_address(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _session_payload(u: User) -> dict:
    return {
        "access_token": create_access_token(u.id, u.role),
        "token_type": "bearer",
        "user": {"id": u.id, "name": u.name, "email": u.email, "role": u.role},
    }


@router.post("/register")
def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    address = _client_address(request)
    register_limiter.check(address, "sign-up")
    register_limiter.record(address)
    if db.query(User).filter(User.email == req.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    u = User(name=req.name, email=req.email.lower(), password_hash=hash_password(req.password), role="farmer")
    db.add(u)
    db.commit()
    db.refresh(u)
    response = _session_payload(u)
    log_event(db, response["user"]["id"], "user_registered")
    return response


@router.post("/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    address = _client_address(request)
    email = req.email.lower()
    account_key = f"{address}|{email}"
    # Refuse early when this e-mail/address, or this address overall, has failed too often.
    login_limiter.check(account_key)
    ip_limiter.check(address)

    u = db.query(User).filter(User.email == email).first()
    # Always do one password check, even for unknown e-mails, so timing does not give them away.
    password_ok = verify_password(req.password, u.password_hash if u else dummy_password_hash())
    if not u or not password_ok:
        login_limiter.record(account_key)
        ip_limiter.record(address)
        # The e-mail address is deliberately NOT stored in the audit trail.
        log_event(db, u.id if u else None, "login_failed")
        raise HTTPException(401, "Invalid email or password")

    # Only the e-mail counter is cleared. The per-address counter is not, otherwise an
    # attacker could log in to their own account to wipe their guessing history.
    login_limiter.reset(account_key)
    response = _session_payload(u)
    log_event(db, response["user"]["id"], "login_succeeded")
    return response
