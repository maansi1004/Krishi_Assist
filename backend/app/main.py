from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import Base, engine
import app.models
from app.api.schemes import router as schemes_router
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.evaluation import router as evaluation_router
from app.api.assistant import router as assistant_router
from app.api.farmer_workspace import router as farmer_workspace_router, canonical_router as workflow_alias_router
from app.api.reports import router as reports_router

Base.metadata.create_all(bind=engine)
app=FastAPI(title="KrishiAssist API",version="0.7.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:5174","http://127.0.0.1:5174"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(schemes_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(evaluation_router)
app.include_router(assistant_router)
app.include_router(farmer_workspace_router)
app.include_router(workflow_alias_router)
app.include_router(reports_router)
@app.get("/")
def root(): return {"service":"KrishiAssist API","status":"ok","docs":"/docs"}

@app.get("/health")
def health(): return {"status":"ok","service":"krishiassist-api","version":"0.7.0"}

@app.get("/api/diagnostics")
def diagnostics():
    from app.services.scheme_service import load_schemes
    return {"status":"ok","schemeCount":len(load_schemes()),"routes":"loaded","service":"krishiassist-api","version":"0.7.0"}
