from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.dependencies import current_user
from app.db.session import get_db
from app.models.user import User
from app.services.audit import log_event
from app.services.need_extraction import extract_need
from app.services.rate_limit import need_limiter
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/need", tags=["need"])


class NeedRequest(BaseModel):
    text: str = Field(min_length=3, max_length=1000)
    language: str = Field(default="en", max_length=12)


@router.post("/extract")
def extract(request: NeedRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Step 1 of the need flow: read the farmer's sentence and SUGGEST details.
    Nothing is saved and no scheme is checked here. The farmer confirms on screen first."""
    key = str(user.id)
    need_limiter.check(key, "need-analysis")
    need_limiter.record(key)
    result = extract_need(request.text, request.language)
    # The sentence itself is not stored; only which kinds of details were found.
    log_event(db, user.id, "need_extracted", {
        "topics": [t["id"] for t in result["topics"]],
        "fields": [f["field"] for f in result["fields"]],
        "used_ai": result["usedAI"],
    })
    return result
