from __future__ import annotations

import re

# Words people use for each scheme. Names, short names, codes and Hindi/Hinglish
# names from schemes.json are added automatically (see scheme_phrases below).
ALIASES = {'AGR-50': ['agr-50', 'tractor', 'tractor subsidy', 'tractor purchase', 'ट्रैक्टर', 'ट्रैक्टर सब्सिडी'],
 'PMFBY': ['pmfby', 'crop insurance', 'crop insurance documents', 'fasal bima', 'फसल बीमा', 'फसल का बीमा'],
 'PM-KISAN': ['pm-kisan',
              'pm kisan',
              'kisan samman',
              'पीएम किसान',
              'किसान सम्मान',
              '₹6000',
              'rs 6000',
              '6000 rupees',
              '6000 per year',
              'किसान सम्मान निधि'],
 'NFSM': ['nfsm', 'food security', 'seed support', 'बीज सहायता', 'खाद्य सुरक्षा'],
 'UK-PMKSY-HKKP': ['pmksy', 'har khet ko pani', 'irrigation', 'irrigation support', 'सिंचाई', 'पानी'],
 'UK-CAP-AROMATIC': ['aromatic', 'aromatic plants', 'सुगंधित पौधे', 'aromatic cultivation'],
 'TN-FIG-001': ['farmer interest group', 'fig', 'farmer group', 'किसान समूह'],
 'AS-MMKSSY': ['krishi sa sajuli', 'assam tools', 'farm tools', 'कृषि सा सजुली', 'कृषि उपकरण'],
 'AGR-2': ['agr-2',
           'farm mechanization',
           'mechanization',
           'machinery',
           'farm machinery',
           'equipment',
           'खेती मशीनरी',
           'मशीनरी',
           'मशीनीकरण',
           'उपकरण'],
 'UK-AGRI-INV-CROP-LOSS': ['crop damage', 'crop loss', '33%', 'फसल नुकसान', 'फसल क्षति'],
 'GJ-AGRI-SKILL': ['skill training', 'agricultural training', 'training', 'कृषि प्रशिक्षण', 'प्रशिक्षण'],
 'PM-KMY': ['pension', 'kisan maan dhan', 'maandhan', 'kisan pension', 'पेंशन', 'किसान पेंशन', 'मानधन'],
 'KCC-MISS': ['kisan credit card',
              'kcc',
              'credit card',
              'crop loan',
              'farm loan',
              'loan',
              'interest subvention',
              'किसान क्रेडिट कार्ड',
              'केसीसी',
              'कृषि ऋण',
              'कर्ज',
              'ऋण'],
 'AIF': ['agriculture infrastructure fund',
         'infrastructure fund',
         'warehouse',
         'cold storage',
         'कृषि अवसंरचना',
         'गोदाम',
         'कोल्ड स्टोरेज'],
 'PDMC': ['per drop more crop',
          'drip irrigation',
          'drip',
          'sprinkler',
          'micro irrigation',
          'ड्रिप',
          'स्प्रिंकलर',
          'सूक्ष्म सिंचाई'],
 'SMAM': ['smam',
          'agricultural mechanization',
          'farm machinery',
          'machinery',
          'mechanization',
          'custom hiring',
          'मशीनरी',
          'मशीनीकरण'],
 'PKVY': ['pkvy', 'paramparagat', 'organic farming', 'organic', 'जैविक खेती', 'जैविक', 'परंपरागत कृषि'],
 'SHC': ['soil health card', 'soil card', 'shc', 'मृदा स्वास्थ्य कार्ड', 'सॉइल हेल्थ कार्ड'],
 'RKVY-SHC-FERT-001': ['soil fertility', 'fertility', 'मृदा उर्वरता'],
 'PM-KUSUM': ['kusum', 'solar pump', 'solar', 'solar panel', 'सौर पंप', 'सोलर पंप', 'सोलर', 'कुसुम'],
 'MIDH': ['midh', 'horticulture', 'horticulture mission', 'orchard', 'बागवानी'],
 'MIDH-NBM': ['bamboo', 'bamboo mission', 'बांस'],
 'RKVY': ['rkvy', 'rashtriya krishi vikas', 'राष्ट्रीय कृषि विकास'],
 'NMNF': ['nmnf', 'natural farming', 'zero budget', 'प्राकृतिक खेती'],
 'NFSM-SEED': ['planting material', 'seed mission', 'seed and planting material', 'बीज और रोपण'],
 'NBHM': ['beekeeping', 'bee keeping', 'honey mission', 'honey', 'मधुमक्खी', 'शहद'],
 'ISAM': ['agricultural marketing', 'marketing', 'mandi', 'enam', 'e nam', 'विपणन', 'मंडी'],
 'RAD-IFS-001': ['rainfed', 'rainfed area', 'integrated farming', 'वर्षा आधारित', 'एकीकृत खेती'],
 'RAD-IFS-GROUP-001': ['integrated farming group', 'farming systems group'],
 'MH-NDKSP-001': ['nanaji deshmukh', 'pocra', 'mahapocra', 'climate resilient', 'नानाजी देशमुख'],
 'MH-NDKSP-FPO-001': ['fpo', 'farmer producer', 'producer organization', 'producer organisation', 'एफपीओ'],
 'SK-COFFEE-EXP-001': ['coffee', 'coffee expansion', 'कॉफी'],
 'GA-VERMICOMPOST-001': ['vermicompost', 'vermi compost', 'केंचुआ खाद', 'वर्मी कंपोस्ट'],
 'GA-BIOGAS-001': ['biogas', 'bio gas', 'बायोगैस'],
 'GA-MANURE-001': ['manure', 'farm waste', 'compost', 'गोबर खाद'],
 'HR-AGRI-PWD-001': ['disability', 'disabled', 'divyang', 'persons with disabilities', 'दिव्यांग', 'विकलांग']}


_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def norm_match(text: str) -> str:
    """Lower-case text, treat - _ / as spaces, drop punctuation. Used for matching."""
    t = str(text).lower()
    t = re.sub(r"[-_/]+", " ", t)
    t = re.sub(r"[^\w\s\u0900-\u097F₹%]", " ", t)
    return " ".join(t.split())


def contains_phrase(text_norm: str, phrase: str) -> bool:
    """True only if `phrase` appears as whole word(s) in `text_norm`.

    'fig' matches 'fig scheme' but NOT 'figure' or 'configure'.
    Hindi phrases use a plain contains check (Hindi words take many endings).
    """
    p = norm_match(phrase)
    if not p:
        return False
    if _DEVANAGARI.search(p):
        return p in text_norm
    return re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", text_norm) is not None


def scheme_phrases(s: dict) -> list[tuple[str, int, bool]]:
    """All the ways a farmer might name this scheme: (phrase, strength, is_official).

    Official names, codes and nicknames taken from the scheme's own name
    (is_official=True) are stronger than loose topic words, and longer phrases
    are stronger than shorter ones.
    """
    out: list[tuple[str, int, bool]] = []

    def add(phrase, base, official):
        n = norm_match(phrase or "")
        if len(n) >= 2:
            out.append((phrase, base + len(n), official))

    for key in ("schemeCode", "shortName", "name"):
        add(str(s.get(key) or ""), 100, True)
    for tr in (s.get("translations") or {}).values():
        add((tr or {}).get("name"), 90, True)
    # A nickname counts as the scheme's real name when it appears inside the scheme's own
    # name (for example 'har khet ko pani' or 'tractor'). Other words ('irrigation',
    # 'crop loss') are loose topic words and are treated more carefully.
    own_names = norm_match(" ".join(filter(None, [s.get("name"), s.get("shortName")] + [(tr or {}).get("name") for tr in (s.get("translations") or {}).values()])))
    for alias in ALIASES.get(s.get("schemeCode"), []):
        add(alias, 50, contains_phrase(own_names, alias))
    return out


def match_info(s: dict, q_norm: str) -> tuple[int, bool]:
    """(strength, named_officially) of the best phrase of this scheme found in the question."""
    best = (0, False)
    for phrase, strength, official in scheme_phrases(s):
        if contains_phrase(q_norm, phrase) and (official, strength) > (best[1], best[0]):
            best = (strength, official)
    return best


def match_strength(s: dict, q_norm: str) -> int:
    return match_info(s, q_norm)[0]


def _state_fit(s: dict, profile: dict) -> int:
    ps = str(profile.get("state") or "").strip().lower()
    ss = str(s.get("state") or "").strip().lower()
    if ps and ss == ps:
        return 2
    if ss == "all india":
        return 1
    return 0


def _other_state_only(s: dict, profile: dict) -> bool:
    """True when the farmer's state is known and this scheme belongs to a different single state."""
    ps = str(profile.get("state") or "").strip().lower()
    ss = str(s.get("state") or "").strip().lower()
    return bool(ps) and ss not in ("", "all india") and ss != ps


def best_scheme_match(q: str, profile: dict, schemes: list[dict]) -> dict | None:
    """The scheme the farmer most clearly named, or None.

    A scheme the farmer names by its real name, code or nickname always counts.
    A scheme found only through a loose topic word (for example 'irrigation') is
    ignored when it belongs to a different state than the farmer's, so a Punjab
    farmer is not answered with an Uttarakhand-only scheme.

    Order: official name first, then strongest match, then the farmer's own state
    (or All India), then schemes whose data is verified.
    """
    qn = norm_match(q)
    ranked = []
    for s in schemes:
        strength, official = match_info(s, qn)
        if strength <= 0:
            continue
        if not official and _other_state_only(s, profile):
            continue
        ranked.append((official, strength, _state_fit(s, profile), s.get("status") == "active", s))
    if not ranked:
        return None
    ranked.sort(key=lambda r: r[:4], reverse=True)
    return ranked[0][4]


def score_scheme(s: dict, q: str, profile: dict) -> int:
    qn = norm_match(q)
    text = " ".join(str(s.get(k, "")) for k in ["name", "shortName", "category", "description"]).lower()
    score = 0
    strength, official = match_info(s, qn)
    # A loose word only counts for schemes the farmer can actually use in their state.
    if strength > 0 and (official or not _other_state_only(s, profile)):
        score += 65
    keyword_groups = {
        "tractor": ["tractor", "farm mechanization", "mechanization", "machinery", "farm machinery", "equipment", "ट्रैक्टर", "मशीनरी", "मशीनीकरण", "उपकरण"],
        "insurance": ["insurance", "crop insurance", "pmfby", "बीमा", "फसल बीमा"],
        "irrigation": ["irrigation", "water", "pmksy", "सिंचाई", "पानी"],
        "seed": ["seed", "planting material", "crop", "बीज", "फसल"],
        "training": ["training", "skill", "capacity", "प्रशिक्षण", "कौशल"],
        "financial": ["financial", "income", "grant", "assistance", "वित्तीय", "अनुदान"],
    }
    for terms in keyword_groups.values():
        if any(contains_phrase(qn, term) for term in terms) and any(term.lower() in text for term in terms):
            score += 25
    state = str(profile.get("state") or "").lower()
    scheme_state = str(s.get("state") or "").lower()
    if state and (scheme_state == state or scheme_state == "all india"):
        score += 30
    if profile.get("primary_crop") and str(profile["primary_crop"]).lower() in text:
        score += 5
    return min(score, 100)
