from fastapi import APIRouter, HTTPException
from app.services.scheme_service import load_schemes, get_scheme
from app.schemas.eligibility import DiscoveryRequest
from app.engines.recommendation_engine import score_scheme, normalize

router = APIRouter(prefix="/api/schemes", tags=["schemes"])

@router.get("")
def schemes():
    return load_schemes()

@router.get("/{scheme_code}")
def scheme(scheme_code: str):
    result = get_scheme(scheme_code)
    if not result:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return result

@router.post("/discover")
def discover(request: DiscoveryRequest):
    profile = request.profile.model_dump() if request.profile else {}
    need = request.need.strip()
    category = (request.category or "").strip().lower()
    results = []
    # Category is an explicit signal; the recommendation engine also understands
    # natural-language terms such as machinery/equipment/tractor in English and Hindi.
    for s in load_schemes():
        score = score_scheme(s, need, profile)
        scheme_category = str(s.get("category", "")).lower()
        if category and category == scheme_category:
            score += 25
        # Friendly fallback for broad category searches.
        q = normalize(need)
        category_terms = {
            "farm_mechanization": ["machinery", "equipment", "mechanization", "tractor", "मशीनरी", "उपकरण", "मशीनीकरण", "ट्रैक्टर"],
            "crop_insurance": ["insurance", "crop insurance", "बीमा", "फसल बीमा"],
            "irrigation": ["irrigation", "water", "सिंचाई", "पानी"],
            "seeds_crops": ["seed", "seeds", "बीज", "crop", "फसल"],
            "training": ["training", "skill", "प्रशिक्षण", "कौशल"],
        }
        for term in category_terms.get(category, []):
            if term in q and term in scheme_category + " " + str(s.get("description", "")).lower():
                score = max(score, 50)
                break
        if score > 0:
            results.append({"scheme": s, "relevanceScore": min(score, 100)})
    results.sort(key=lambda x: x["relevanceScore"], reverse=True)
    return results[:10]
