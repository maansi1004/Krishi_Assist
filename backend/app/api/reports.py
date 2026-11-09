from __future__ import annotations

import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user
from app.db.session import get_db
from app.models.profile import FarmProfile
from app.models.user import User
from app.schemas.profile import FarmerProfile
from app.services.scheme_service import get_scheme
from app.engines.eligibility_engine import evaluate_scheme

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Fix 3: use EVERY profile field, exactly like the app's eligibility check does,
# so the PDF can never disagree with what the farmer saw on screen.
PROFILE_FIELDS = list(FarmerProfile.model_fields.keys())

def _profile(row: FarmProfile | None) -> dict:
    if not row:
        return {}
    return {f: getattr(row, f) for f in PROFILE_FIELDS}

def _text(value) -> str:
    if value is None: return "—"
    if isinstance(value, dict):
        return str(value.get("description") or value.get("name") or value.get("benefitType") or value)
    return str(value)

@router.get("/scheme/{scheme_code}")
def scheme_report(scheme_code: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    scheme = get_scheme(scheme_code)
    if not scheme:
        raise HTTPException(404, "Scheme not found")
    profile_row = db.query(FarmProfile).filter_by(user_id=user.id).first()
    profile = _profile(profile_row)
    result = evaluate_scheme(scheme, profile)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("KA_Title", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=14)
    heading = ParagraphStyle("KA_Heading", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6)
    body = styles["BodyText"]
    story = [Paragraph("KrishiAssist", title), Paragraph("Personalized Agricultural Support Report", heading)]
    story += [Paragraph(f"Scheme: {_text(scheme.get('name'))} ({scheme_code})", body),
              Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body), Spacer(1, 8)]
    story.append(Paragraph("Farmer profile", heading))
    profile_rows = [[k.replace("_", " ").title(), _text(v)] for k,v in profile.items()
                    if v not in (None, [], {}) and k != "extra_attributes"]
    if profile_rows:
        table = Table(profile_rows, colWidths=[150, 330])
        table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.3,colors.grey),("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(table)
    else:
        story.append(Paragraph("No saved farm profile was available. Eligibility cannot be personalized without profile information.", body))

    story.append(Paragraph("Eligibility result", heading))
    story.append(Paragraph(result["status"].replace("_", " "), body))
    criteria_rows = [["Criterion", "Result", "Actual"]]
    for c in result.get("criteria", [])[:12]:
        criteria_rows.append([_text(c.get("criterion")), _text(c.get("result")), _text(c.get("actual"))])
    table = Table(criteria_rows, colWidths=[300, 75, 105], repeatRows=1)
    table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.3,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(table)

    for title_text, items in [("Benefits", scheme.get("benefits", [])), ("Documents", scheme.get("documents", [])), ("Application steps", scheme.get("actionSteps", []))]:
        story.append(Paragraph(title_text, heading))
        if items:
            for i,item in enumerate(items[:12], 1):
                story.append(Paragraph(f"{i}. {_text(item)}", body))
        else:
            story.append(Paragraph("Verify this information from the official source.", body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Important: Eligibility is based on the information provided and the structured scheme criteria. Final approval is subject to the implementing authority. This report does not submit a government application.", body))
    doc.build(story)
    buf.seek(0)
    filename = f"KrishiAssist_{scheme_code}_report.pdf"
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
