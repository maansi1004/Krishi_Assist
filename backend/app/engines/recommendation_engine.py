from __future__ import annotations

ALIASES = {
    "AGR-50": ["agr-50", "tractor", "tractor subsidy", "tractor purchase", "ट्रैक्टर", "ट्रैक्टर सब्सिडी"],
    "PMFBY": ["pmfby", "crop insurance", "crop insurance documents", "fasal bima", "फसल बीमा", "फसल का बीमा"],
    "PM-KISAN": ["pm-kisan", "pm kisan", "kisan samman", "6000", "पीएम किसान", "किसान सम्मान"],
    "NFSM": ["nfsm", "food security", "seed support", "बीज सहायता", "खाद्य सुरक्षा"],
    "UK-PMKSY-HKKP": ["pmksy", "har khet ko pani", "irrigation", "irrigation support", "सिंचाई", "पानी"],
    "UK-CAP-AROMATIC": ["aromatic", "aromatic plants", "सुगंधित पौधे", "aromatic cultivation"],
    "TN-FIG-001": ["farmer interest group", "fig", "farmer group", "किसान समूह"],
    "AS-MMKSSY": ["krishi sa sajuli", "assam tools", "farm tools", "कृषि सा सजुली", "कृषि उपकरण"],
    "AGR-2": ["agr-2", "farm mechanization", "mechanization", "machinery", "farm machinery", "equipment", "खेती मशीनरी", "मशीनरी", "मशीनीकरण", "उपकरण"],
    "UK-AGRI-INV-CROP-LOSS": ["crop damage", "crop loss", "33%", "फसल नुकसान", "फसल क्षति"],
    "GJ-AGRI-SKILL": ["skill training", "agricultural training", "training", "कृषि प्रशिक्षण", "प्रशिक्षण"],
}


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def score_scheme(s: dict, q: str, profile: dict) -> int:
    qn = normalize(q)
    text = " ".join(str(s.get(k, "")) for k in ["name", "shortName", "category", "description"]).lower()
    score = 0
    for code, terms in ALIASES.items():
        if code == s.get("schemeCode") and any(term.lower() in qn for term in terms):
            score += 65
            break
    keyword_groups = {
        "tractor": ["tractor", "farm mechanization", "mechanization", "machinery", "farm machinery", "equipment", "ट्रैक्टर", "मशीनरी", "मशीनीकरण", "उपकरण"],
        "insurance": ["insurance", "crop insurance", "pmfby", "बीमा", "फसल बीमा"],
        "irrigation": ["irrigation", "water", "pmksy", "सिंचाई", "पानी"],
        "seed": ["seed", "planting material", "crop", "बीज", "फसल"],
        "training": ["training", "skill", "capacity", "प्रशिक्षण", "कौशल"],
        "financial": ["financial", "income", "grant", "assistance", "वित्तीय", "अनुदान"],
    }
    for terms in keyword_groups.values():
        if any(term in qn for term in terms) and any(term.lower() in text for term in terms):
            score += 25
    state = str(profile.get("state") or "").lower()
    scheme_state = str(s.get("state") or "").lower()
    if state and (scheme_state == state or scheme_state == "all india"):
        score += 30
    if profile.get("primary_crop") and str(profile["primary_crop"]).lower() in text:
        score += 5
    return min(score, 100)
