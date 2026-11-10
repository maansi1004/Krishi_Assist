"""The kinds of document a farmer can upload, and how the document names written in the
scheme data (for example "Aadhaar" or "Land documents") map onto them."""
from __future__ import annotations

DOCUMENT_TYPES = [
    {"id": "aadhaar", "label": {"en": "Aadhaar", "hi": "आधार", "hinglish": "Aadhaar"}},
    {"id": "identity_proof", "label": {"en": "Other photo ID", "hi": "अन्य फोटो पहचान पत्र", "hinglish": "Doosra photo ID"}},
    {"id": "land_record", "label": {"en": "Land record or lease", "hi": "ज़मीन का रिकॉर्ड या पट्टा", "hinglish": "Zameen record ya lease"}},
    {"id": "bank_passbook", "label": {"en": "Bank passbook or details", "hi": "बैंक पासबुक या विवरण", "hinglish": "Bank passbook ya details"}},
    {"id": "photo", "label": {"en": "Passport photograph", "hi": "पासपोर्ट फोटो", "hinglish": "Passport photo"}},
    {"id": "ration_card", "label": {"en": "Ration card", "hi": "राशन कार्ड", "hinglish": "Ration card"}},
    {"id": "caste_certificate", "label": {"en": "Caste certificate", "hi": "जाति प्रमाण पत्र", "hinglish": "Jati praman patra"}},
    {"id": "disability_certificate", "label": {"en": "Disability certificate", "hi": "दिव्यांगता प्रमाण पत्र", "hinglish": "Divyangta praman patra"}},
    {"id": "soil_health_card", "label": {"en": "Soil Health Card", "hi": "मृदा स्वास्थ्य कार्ड", "hinglish": "Soil Health Card"}},
    {"id": "age_proof", "label": {"en": "Age proof", "hi": "आयु प्रमाण", "hinglish": "Aayu praman"}},
    {"id": "residence_proof", "label": {"en": "Residence or domicile proof", "hi": "निवास प्रमाण", "hinglish": "Niwas praman"}},
    {"id": "project_documents", "label": {"en": "Project, estimate or invoice", "hi": "परियोजना, अनुमान या बिल", "hinglish": "Project, estimate ya bill"}},
    {"id": "other", "label": {"en": "Other supporting document", "hi": "अन्य सहायक दस्तावेज़", "hinglish": "Anya sahayak document"}},
]
TYPE_IDS = {t["id"] for t in DOCUMENT_TYPES}

# An Aadhaar card is a photo ID, so it also satisfies a request for "identity proof".
SATISFIED_BY = {"identity_proof": ["identity_proof", "aadhaar"]}


def suggest_type(name: str) -> str:
    """Best guess of the document type for a document name from the scheme data."""
    n = (name or "").lower()
    if "aadhaar" in n:
        return "aadhaar"
    if "ration card" in n:
        return "ration_card"
    if "caste" in n:
        return "caste_certificate"
    if "disability" in n:
        return "disability_certificate"
    if "soil health" in n:
        return "soil_health_card"
    if "age proof" in n:
        return "age_proof"
    if "residence" in n or "domicile" in n:
        return "residence_proof"
    if "photo id" in n or "photo identity" in n:
        return "identity_proof"
    if "photograph" in n or "passport photo" in n:
        return "photo"
    if any(w in n for w in ("land", "tenancy", "tenure", "lease", "khasra", "possession")):
        return "land_record"
    if "identity" in n or n.endswith(" id") or "government id" in n:
        return "identity_proof"
    if any(w in n for w in ("bank", "passbook", "ifsc")):
        return "bank_passbook"
    if any(w in n for w in ("dpr", "estimate", "proposal", "invoice", "cost", "model design")):
        return "project_documents"
    return "other"


def satisfying_types(doc_type: str) -> list[str]:
    return SATISFIED_BY.get(doc_type, [doc_type])


def used_by_schemes(schemes: list[dict]) -> dict[str, int]:
    """How many schemes ask for each kind of document (required ones only).
    A document that satisfies a request counts too: an Aadhaar upload also answers "identity proof"."""
    counts = {t["id"]: 0 for t in DOCUMENT_TYPES}
    for scheme in schemes:
        asked = {suggest_type(d["name"]) for d in scheme.get("documents", []) if d.get("requiredType") == "required"}
        helped = {t for a in asked for t in satisfying_types(a)}
        for t in helped:
            counts[t] = counts.get(t, 0) + 1
    return counts
