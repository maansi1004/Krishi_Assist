from __future__ import annotations
import json
import urllib.request
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import optional_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.profile import FarmProfile
from app.models.user import User
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.schemas.profile import FarmerProfile
from app.services.scheme_service import load_schemes, get_scheme
from app.engines.eligibility_engine import evaluate_scheme
from app.engines.recommendation_engine import ALIASES, normalize, score_scheme

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
KB_FILE = Path(__file__).resolve().parents[3] / "data/knowledge_base/agriculture_knowledge.json"


def profile_dict(row: FarmProfile | None) -> dict:
    if not row:
        return {}
    return {f: getattr(row, f) for f in FarmerProfile.model_fields.keys()}


def classify(message: str) -> str:
    q = normalize(message)
    if any(x in q for x in ["eligible", "eligibility", "qualify", "am i allowed", " पात्र", "पात्र", "योग्य", "eligible"]):
        return "eligibility"
    if any(x in q for x in ["document", "documents", "paper", "papers", "दस्तावेज", "कागज"]):
        return "documents"
    if any(x in q for x in ["benefit", "benefits", "amount", "how much", "लाभ", "कितना", "मिलेगा"]):
        return "benefits"
    if any(x in q for x in ["how to apply", "apply", "application", "application process", "आवेदन", "आवेदन कैसे", "प्रक्रिया", "कदम"]):
        return "application"
    if any(x in q for x in ["scheme", "schemes", "subsidy", "support", "yojana", "योजना", "सब्सिडी", "सहायता", "मदद"]):
        return "scheme_discovery"
    return "general_agriculture_support"



def relevant_schemes(q: str, profile: dict) -> list[dict]:
    scored = []
    for s in load_schemes():
        score = score_scheme(s, q, profile)
        if score > 0:
            scored.append({"schemeCode": s["schemeCode"], "name": s["name"], "state": s.get("state"), "category": s.get("category"), "relevanceScore": score})
    scored.sort(key=lambda x: x["relevanceScore"], reverse=True)
    return scored[:6]


def find_scheme_for_question(q: str, profile: dict, context_scheme_code: str | None = None) -> dict | None:
    """Resolve the scheme for a question without letting stale UI context override an explicit request."""
    qn = normalize(q)

    # 1. Explicit scheme aliases always win.
    for code, terms in ALIASES.items():
        if any(term.lower() in qn for term in terms):
            return get_scheme(code)

    # 2. Exact scheme names/codes in the question.
    for s in load_schemes():
        values = [s.get("schemeCode"), s.get("name"), s.get("shortName")]
        if any(v and normalize(str(v)) in qn for v in values):
            return s

    # 3. Only then use the selected scheme as conversational context.
    if context_scheme_code:
        contextual = get_scheme(context_scheme_code.strip())
        if contextual:
            return contextual

    # 4. Finally use relevance ranking.
    matches = relevant_schemes(q, profile)
    return get_scheme(matches[0]["schemeCode"]) if matches and matches[0]["relevanceScore"] >= 35 else None


def lang_text(language: str, en: str, hi: str, hinglish: str) -> str:
    if language == "hi": return hi
    if language == "hinglish": return hinglish
    return en


def load_kb() -> list[dict]:
    try:
        return json.loads(KB_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def general_answer(q: str, language: str, profile: dict) -> str | None:
    qn = normalize(q)
    for item in load_kb():
        if any(term.lower() in qn for term in item.get("keywords", [])):
            return item.get("answers", {}).get(language) or item.get("answers", {}).get("en")
    # Optional grounded LLM fallback. It receives only the minimum farm context and verified scheme excerpts.
    if settings.openrouter_api_key and settings.llm_model:
        context = {"profile": {k: profile.get(k) for k in ["state", "district", "primary_crop", "land_size_hectares", "irrigation_type"] if profile.get(k) is not None}, "schemes": [{"code": s["schemeCode"], "name": s["name"], "description": s.get("description"), "benefits": s.get("benefits", [])[:3]} for s in load_schemes()]}
        system = "You are KrishiAssist, a farmer-friendly agricultural support assistant. Answer in the requested language. Use the supplied scheme context only for scheme claims. Never invent eligibility, benefits, official links, deadlines or documents. For personal eligibility, say that the deterministic rule engine must evaluate the scheme. For general agriculture advice, give practical, cautious guidance and state when local agronomist/official advice is needed."
        payload = json.dumps({"model": settings.llm_model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps({"language": language, "question": q, "context": context}, ensure_ascii=False)}], "temperature": 0.2}).encode()
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload, headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json", "HTTP-Referer": "http://localhost:5173", "X-Title": "KrishiAssist"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None
    return None


@router.post("/chat", response_model=AssistantChatResponse)
def chat(request: AssistantChatRequest, user: User | None = Depends(optional_current_user), db: Session = Depends(get_db)):
    profile = profile_dict(db.query(FarmProfile).filter_by(user_id=user.id).first()) if user else {}
    q = request.message.strip()
    intent = classify(q)
    # Use previous scheme context only for follow-up questions. A new/general
    # question must be free to select a different topic.
    follow_up_intent = intent in {"documents", "benefits", "application", "eligibility"}
    selected = find_scheme_for_question(q, profile, request.context_scheme_code if follow_up_intent else None)
    schemes = relevant_schemes(q, profile)
    profile_used = bool(profile)

    if intent == "documents":
        if selected and selected.get("documents"):
            selected_name = selected.get("translations", {}).get(request.language, {}).get("name") or selected["name"]
            docs = [d if isinstance(d, str) else d.get("name", d.get("document", "Document")) for d in selected["documents"]]
            reply = lang_text(request.language,
                f"For {selected_name}, the verified scheme record lists: " + "; ".join(docs) + ". Final requirements should be confirmed from the official source.",
                f"{selected_name} के सत्यापित रिकॉर्ड में ये दस्तावेज़ दिए गए हैं: " + "; ".join(docs) + ". अंतिम आवश्यकताएं आधिकारिक स्रोत से जांचें।",
                f"{selected_name} ke verified record mein ye documents diye gaye hain: " + "; ".join(docs) + ". Final requirements official source se confirm karein.")
        else:
            reply = lang_text(request.language, "Tell me the scheme or support you mean, for example crop insurance, tractor subsidy or irrigation.", "योजना या सहायता का नाम बताएं, जैसे फसल बीमा, ट्रैक्टर सब्सिडी या सिंचाई।", "Scheme ya support bataiye, jaise crop insurance, tractor subsidy ya irrigation.")
    elif intent == "benefits":
        if selected and selected.get("benefits"):
            selected_name = selected.get("translations", {}).get(request.language, {}).get("name") or selected["name"]
            items = [b if isinstance(b, str) else b.get("description", b.get("benefitType", str(b))) for b in selected["benefits"][:5]]
            reply = lang_text(request.language,
                f"For {selected_name}, the verified record says: " + " ".join(items),
                f"{selected_name} के सत्यापित रिकॉर्ड के अनुसार: " + " ".join(items),
                f"{selected_name} ke verified record ke hisaab se: " + " ".join(items))
        else:
            reply = lang_text(request.language, "Tell me the scheme name or support you mean and I’ll explain its verified benefits.", "योजना या सहायता का नाम बताएं; मैं उसके सत्यापित लाभ बताऊंगा।", "Scheme ya support ka naam bataiye; main verified benefits bataunga.")
    elif intent == "application":
        if selected and selected.get("actionSteps"):
            selected_name = selected.get("translations", {}).get(request.language, {}).get("name") or selected["name"]
            steps = []
            for step in selected["actionSteps"][:6]:
                steps.append(f"{step.get('step')}. {step.get('title')}: {step.get('description')}")
            reply = lang_text(request.language, f"Application steps for {selected_name}: " + " ".join(steps), f"{selected_name} के आवेदन के कदम: " + " ".join(steps), f"{selected_name} ke application steps: " + " ".join(steps))
        else:
            reply = lang_text(request.language, "Tell me the scheme you want to apply for and I’ll explain the verified steps.", "जिस योजना के लिए आवेदन करना है उसका नाम बताएं; मैं सत्यापित कदम बताऊंगा।", "Jis scheme ke liye apply karna hai uska naam bataiye; main verified steps bataunga.")
    elif intent == "eligibility":
        if not user:
            reply = lang_text(request.language, "Please sign in and save your farm profile first. Then I can evaluate your eligibility against the scheme rules.", "पहले साइन इन करके अपनी फार्म प्रोफाइल सेव करें। उसके बाद मैं योजना के नियमों के आधार पर पात्रता जांच सकता हूं।", "Pehle sign in karke apni farm profile save karein. Uske baad main scheme rules ke basis par eligibility check karunga.")
        elif not profile:
            reply = lang_text(request.language, "Your farm profile is empty. Complete My Farm Profile first; I will not guess missing information.", "आपकी फार्म प्रोफाइल खाली है। पहले My Farm Profile पूरा करें; मैं missing information का अनुमान नहीं लगाऊंगा।", "Aapki farm profile empty hai. Pehle My Farm Profile complete karein; main missing information guess nahi karunga.")
        elif selected:
            result = evaluate_scheme(selected, profile)
            status_map = {"ELIGIBLE": ("Eligible", "पात्र", "Eligible"), "ALMOST_ELIGIBLE": ("Almost eligible", "लगभग पात्र", "Almost eligible"), "NOT_ELIGIBLE": ("Not eligible", "पात्र नहीं", "Eligible nahi"), "VERIFICATION_REQUIRED": ("Verification required", "सत्यापन आवश्यक", "Verification zaroori hai")}
            status = status_map.get(result["status"], (result["status"], result["status"], result["status"]))[0 if request.language == "en" else 1 if request.language == "hi" else 2]
            passed = [c["criterion"] for c in result["criteria"] if c["result"] == "PASS"][:4]
            missing = result["missingRequirements"][:4]
            failed = result["failedRequirements"][:4]
            reply = f"{selected['name']}: {status}. "
            if passed: reply += "Passed: " + "; ".join(passed) + ". "
            if missing: reply += "Information needed: " + "; ".join(missing) + ". "
            if failed: reply += "Failed or verification issues: " + "; ".join(failed) + ". "
            reply += "This result comes from the structured rule engine, not an AI guess."
            return AssistantChatResponse(reply=reply, intent=intent, schemes=schemes, profile_used=profile_used, eligibility=result)
        else:
            reply = lang_text(request.language, "Tell me which scheme you mean, for example ‘Am I eligible for tractor subsidy?’", "किस योजना की पात्रता जाननी है बताएं, जैसे ‘क्या मैं ट्रैक्टर सब्सिडी के लिए पात्र हूं?’", "Kaunsi scheme ki eligibility check karni hai bataiye, jaise ‘Am I eligible for tractor subsidy?’")
    elif intent == "scheme_discovery":
        if schemes:
            top = schemes[:5]
            labels = []
            for x in top:
                full = get_scheme(x["schemeCode"])
                tr = (full or {}).get("translations", {}).get(request.language, {}) if full else {}
                name = tr.get("name") or x["name"]
                labels.append(f"{name} ({x['schemeCode']})")
            reply = lang_text(request.language,
                "I found these schemes related to your request: " + ", ".join(labels) + ". They are relevance matches, not an eligibility decision. Ask me about a scheme's benefits, documents, application steps, or whether you qualify.",
                "आपकी जरूरत से संबंधित ये योजनाएं मिलीं: " + ", ".join(labels) + "। ये केवल संबंधित योजनाएं हैं, पात्रता का अंतिम निर्णय नहीं। आप किसी योजना के लाभ, दस्तावेज़, आवेदन प्रक्रिया या अपनी पात्रता के बारे में पूछ सकते हैं।",
                "Aapki need se related ye schemes mili hain: " + ", ".join(labels) + ". Ye relevance matches hain, final eligibility decision nahi. Aap benefits, documents, application steps ya eligibility pooch sakte hain.")
        else:
            reply = lang_text(request.language, "I could not find a matching scheme in the current verified dataset. Try words such as tractor, machinery, crop insurance, irrigation, seeds or training.", "वर्तमान सत्यापित डेटासेट में मिलती हुई योजना नहीं मिली। ट्रैक्टर, मशीनरी, फसल बीमा, सिंचाई, बीज या प्रशिक्षण जैसे शब्दों से पूछें।", "Current verified dataset mein matching scheme nahi mili. Tractor, machinery, crop insurance, irrigation, seeds ya training jaise words try karein.")
    else:
        if selected:
            tr = selected.get("translations", {}).get(request.language, {})
            name = tr.get("name") or selected.get("name")
            category = tr.get("category") or str(selected.get("category") or "agriculture").replace("_", " ")
            summary = tr.get("description") or selected.get("description") or "Government agricultural support programme."
            reply = lang_text(request.language,
                f"{name} is a {category} support programme. {summary} Ask me about its eligibility, benefits, documents or application steps.",
                f"{name} {category} से जुड़ी योजना है। {summary} आप इसकी पात्रता, लाभ, दस्तावेज़ या आवेदन के कदम पूछ सकते हैं।",
                f"{name} ek {category} support scheme hai. {summary} Aap iski eligibility, benefits, documents ya application steps pooch sakte hain.")
        else:
            reply = general_answer(q, request.language, profile)
        if not reply:
            reply = lang_text(request.language,
                "I can answer agriculture questions, explain verified schemes, list documents and evaluate eligibility when your profile is saved. Tell me your crop, problem or support need.",
                "मैं कृषि से जुड़े सामान्य सवालों, सत्यापित योजनाओं, दस्तावेज़ों और आपकी सेव प्रोफाइल के आधार पर पात्रता में मदद कर सकता हूं। अपनी फसल, समस्या या सहायता की जरूरत बताएं।",
                "Main agriculture questions, verified schemes, documents aur saved profile ke basis par eligibility mein help kar sakta hoon. Apni crop, problem ya support need bataiye.")
    return AssistantChatResponse(reply=reply, intent=intent, schemes=schemes, profile_used=profile_used)
