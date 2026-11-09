"""Checks that every updated KrishiAssist file has the RIGHT content.

Run from the ka folder:   python check_files.py
Prints OK or WRONG for each file. A WRONG file usually means the content of a
different file was pasted into it.
"""
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent

# path -> (text that MUST be inside, text that must NOT be inside)
CHECKS = {
    "backend/app/main.py": (["include_router(matches_router)", "include_router(audit_router)", "include_router(need_router)", "include_router(admin_router)", "settings.cors_origin_list"], []),
    "backend/app/services/llm.py": (["def ask_llm("], []),
    "backend/app/services/need_extraction.py": (["def extract_need(", "AI_FORBIDDEN_FIELDS"], []),
    "backend/app/services/scheme_admin.py": (["def coverage_report(", "def refresh_overrides("], []),
    "backend/app/api/need.py": (['APIRouter(prefix="/api/need"', "def extract("], []),
    "backend/app/api/admin.py": (['APIRouter(prefix="/api/admin"', "def update_scheme(", "require_admin"], []),
    "backend/app/models/scheme_override.py": (["class SchemeOverride"], []),
    "backend/app/models/__init__.py": (["SchemeOverride"], []),
    "backend/app/scripts/make_admin.py": (["def set_role(", "--revoke"], []),
    "backend/app/scripts/__init__.py": ([], []),
    "backend/app/auth/dependencies.py": (["def require_admin(", "def current_user("], []),
    "frontend/src/need.tsx": (["export function NeedPage"], []),
    "frontend/src/activity.tsx": (["export function ActivityPage", "export function describeEvent"], []),
    "frontend/src/admin.tsx": (["export function AdminPage"], []),
    "tests/test_phase10_need.py": (["test_ai_can_never_supply_caste_or_gender"], []),
    "tests/test_phase11_admin.py": (["test_only_admins_can_use_admin_endpoints"], []),
    "backend/app/core/config.py": (["_production_needs_a_real_secret", "DEFAULT_DEV_SECRET"], []),
    "backend/app/auth/security.py": (["def dummy_password_hash(", "'require': ['exp', 'sub']"], []),
    "backend/app/services/rate_limit.py": (["class FailureLimiter", "need_limiter", "ALL_LIMITERS"], []),
    ".env.example": (["APP_ENV=", "CORS_ORIGINS="], ["EMBEDDING_API_KEY", "RAG_MODEL"]),
    "tests/conftest.py": (["fresh_rate_limits", "clean_scheme_overrides", "krishiassist_tests_"], []),
    "tests/test_phase9_security.py": (["test_five_wrong_passwords_lock_that_account_even_for_the_right_password"], []),
    "backend/app/api/audit.py": (['APIRouter(prefix="/api/audit"', "def my_audit_trail("], []),
    "backend/app/api/evaluation.py": (["def history_detail(", "rule_fingerprint"], []),
    "backend/app/api/auth.py": (["login_limiter", "dummy_password_hash", "def register("], []),
    "backend/app/api/profile.py": (["fields_changed", "def create_profile("], []),
    "backend/app/api/farmer_workspace.py": (["ApplicationStatus", "def create_application(", "canonical_router"], []),
    "backend/app/services/application_status.py": (["APPLICATION_STATUSES", '"Under Verification"'], []),
    "backend/app/services/audit.py": (["def log_event("], []),
    "backend/app/services/versioning.py": (["def rule_fingerprint(", "def scheme_version("], []),
    "backend/app/api/matches.py": (['APIRouter(prefix="/api/matches"', "def my_matches("], []),
    "backend/app/api/assistant.py": (["def _readable(", "best_scheme_match"], []),
    "backend/app/api/reports.py": (["PROFILE_FIELDS = list(FarmerProfile.model_fields.keys())"], []),
    "backend/app/engines/eligibility_engine.py": (["def _norm(", "unverifiedScheme"], []),
    "backend/app/engines/recommendation_engine.py": (["def match_info(", "def best_scheme_match("], []),
    "backend/app/schemas/eligibility.py": (["class EligibilityRequest", "class DiscoveryRequest"], ["APIRouter"]),
    "backend/app/services/profile_service.py": (["def profile_completeness("], []),
    "backend/app/services/scheme_service.py": (["def set_overrides(", "def load_all_schemes(", "def load_schemes("], ["from app.services.scheme_service import"]),
    "frontend/src/main.tsx": (["function App(", "MatchesPage", "NeedPage", "ActivityPage", "AdminPage"], []),
    "frontend/src/matches.tsx": (["export function MatchesPage", "export function MatchResults", "export function CompletenessBanner"], []),
    "frontend/src/questions.tsx": (["export function QuestionsForm", "export function ProfileSelect"], []),
    "frontend/src/styles.css": ([".matchesLink", ".questionsPanel"], []),
    "tests/test_scheme_models.py": (["len({m.schemeCode"], []),
    "tests/test_phase5_matching.py": (["test_text_matching_ignores_case_spaces_and_underscores"], []),
    "tests/test_phase6_assistant.py": (["test_scheme_file_is_loaded_once_and_reused"], []),
    "tests/test_phase7_matches.py": (["test_completeness_lists_what_is_missing", "def new_farmer("], []),
    "tests/test_phase8_audit.py": (["test_exactly_the_seven_statuses_from_the_report_are_allowed", "def trail("], []),
}

bad = 0
for rel, (must, must_not) in CHECKS.items():
    path = BASE / rel
    if not path.exists():
        print(f"MISSING  {rel}")
        bad += 1
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    problems = [f"does not contain: {m}" for m in must if m not in text]
    problems += [f"should NOT contain: {m}" for m in must_not if m in text]
    if problems:
        bad += 1
        first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "(empty file)")
        print(f"WRONG    {rel}\n           {problems[0]}\n           file starts with: {first[:90]}")
    else:
        print(f"OK       {rel}")

old = BASE / "backend/app/api/eligibility.py"
if old.exists():
    print("NOTE     backend/app/api/eligibility.py is an old unused file. You can delete it.")

print()
if bad:
    print(f"{bad} file(s) need fixing. Copy them again from the zip.")
    sys.exit(1)
print("All files are correct.")
