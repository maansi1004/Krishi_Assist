from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base, engine
import app.models
from app.api.schemes import router as schemes_router
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.evaluation import router as evaluation_router
from app.api.assistant import router as assistant_router
from app.api.farmer_workspace import router as farmer_workspace_router, canonical_router as workflow_alias_router
from app.api.reports import router as reports_router
from app.api.matches import router as matches_router
from app.api.audit import router as audit_router
from app.api.need import router as need_router
from app.api.admin import router as admin_router
from app.api.documents import router as documents_router

Base.metadata.create_all(bind=engine)
# Load the administrator's scheme decisions (switched-off / verified schemes) into memory.
from app.db.session import SessionLocal
from app.services.scheme_admin import refresh_overrides
with SessionLocal() as _db:
    refresh_overrides(_db)
# In production the interactive docs and the OpenAPI file are switched off.
docs = {} if not settings.is_production else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app=FastAPI(title="KrishiAssist API",version="0.7.0",**docs)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(schemes_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(evaluation_router)
app.include_router(assistant_router)
app.include_router(farmer_workspace_router)
app.include_router(workflow_alias_router)
app.include_router(reports_router)
app.include_router(matches_router)
app.include_router(audit_router)
app.include_router(need_router)
app.include_router(admin_router)
app.include_router(documents_router)
@app.get("/")
def root(): return {"service":"KrishiAssist API","status":"ok","docs":"/docs"}

@app.get("/health")
def health(): return {"status":"ok","service":"krishiassist-api","version":"0.7.0"}

@app.get("/api/diagnostics")
def diagnostics():
    from app.services.scheme_service import load_schemes
    return {"status":"ok","schemeCount":len(load_schemes()),"routes":"loaded","service":"krishiassist-api","version":"0.7.0"}
