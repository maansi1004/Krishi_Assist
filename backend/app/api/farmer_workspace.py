from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.saved_scheme import SavedScheme
from app.models.user import User
from app.services.scheme_service import get_scheme

router = APIRouter(prefix="/api/farmer", tags=["farmer workspace"])

class SaveSchemeRequest(BaseModel):
    scheme_code: str = Field(min_length=1, max_length=80)

class ApplicationRequest(BaseModel):
    scheme_code: str = Field(min_length=1, max_length=80)
    status: str = "Planning"
    notes: str | None = None

class ApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None

@router.get("/saved-schemes")
def list_saved(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(SavedScheme).filter_by(user_id=user.id).order_by(SavedScheme.saved_at.desc()).all()
    return [{"id": r.id, "schemeCode": r.scheme_code, "applicationStatus": r.application_status, "savedAt": r.saved_at} for r in rows]

@router.post("/saved-schemes")
def save_scheme(request: SaveSchemeRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not get_scheme(request.scheme_code):
        raise HTTPException(404, "Scheme not found")
    existing = db.query(SavedScheme).filter_by(user_id=user.id, scheme_code=request.scheme_code).first()
    if existing:
        return {"id": existing.id, "schemeCode": existing.scheme_code, "saved": True}
    row = SavedScheme(user_id=user.id, scheme_code=request.scheme_code)
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "schemeCode": row.scheme_code, "saved": True}

@router.delete("/saved-schemes/{scheme_code}")
def delete_saved(scheme_code: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(SavedScheme).filter_by(user_id=user.id, scheme_code=scheme_code).first()
    if row: db.delete(row); db.commit()
    return {"deleted": True}

@router.get("/applications")
def list_applications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Application).filter_by(user_id=user.id).order_by(Application.updated_at.desc()).all()
    return [{"id": r.id, "schemeCode": r.scheme_code, "status": r.status, "notes": r.notes, "updatedAt": r.updated_at} for r in rows]

@router.post("/applications")
def create_application(request: ApplicationRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not get_scheme(request.scheme_code): raise HTTPException(404, "Scheme not found")
    row = Application(user_id=user.id, scheme_code=request.scheme_code, status=request.status, notes=request.notes, updated_at=datetime.now(timezone.utc))
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "schemeCode": row.scheme_code, "status": row.status, "notes": row.notes}

@router.put("/applications/{application_id}")
def update_application(application_id: int, request: ApplicationUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(Application).filter_by(id=application_id, user_id=user.id).first()
    if not row: raise HTTPException(404, "Application not found")
    if request.status is not None: row.status = request.status
    if request.notes is not None: row.notes = request.notes
    row.updated_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(row)
    return {"id": row.id, "schemeCode": row.scheme_code, "status": row.status, "notes": row.notes}


# Canonical API aliases. These keep the public contract stable while preserving
# the legacy /api/farmer/* endpoints used by older frontend builds.
canonical_router = APIRouter(prefix="/api", tags=["workflow aliases"])

@canonical_router.get("/saved-schemes")
def canonical_list_saved(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list_saved(user, db)

@canonical_router.post("/saved-schemes")
def canonical_save_scheme(request: SaveSchemeRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return save_scheme(request, user, db)

@canonical_router.delete("/saved-schemes/{scheme_code}")
def canonical_delete_saved(scheme_code: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return delete_saved(scheme_code, user, db)

@canonical_router.get("/applications")
def canonical_list_applications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list_applications(user, db)

@canonical_router.post("/applications")
def canonical_create_application(request: ApplicationRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return create_application(request, user, db)

@canonical_router.put("/applications/{application_id}")
def canonical_update_application(application_id: int, request: ApplicationUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return update_application(application_id, request, user, db)
