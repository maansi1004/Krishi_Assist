import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.api.auth as auth_api
from app.core.config import DEFAULT_DEV_SECRET, PROJECT_ROOT, Settings, settings
from app.db.session import engine
from app.main import app
from app.services.rate_limit import FailureLimiter

client = TestClient(app)
PASSWORD = "StrongPass123"


def register():
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"name": "Test Farmer", "email": email, "password": PASSWORD})
    assert r.status_code == 200
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


def login(email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ---------- settings ----------

def test_production_refuses_the_built_in_development_secret():
    with pytest.raises(ValueError):
        Settings(app_env="production", jwt_secret=DEFAULT_DEV_SECRET)


def test_production_refuses_a_short_secret_but_accepts_a_long_one():
    with pytest.raises(ValueError):
        Settings(app_env="production", jwt_secret="short")
    assert Settings(app_env="production", jwt_secret="x" * 40).is_production is True


def test_development_may_use_the_built_in_secret():
    assert Settings(app_env="development", jwt_secret=DEFAULT_DEV_SECRET).is_production is False


def test_relative_sqlite_path_always_means_inside_the_project_folder():
    expected = f"sqlite:///{(PROJECT_ROOT / 'krishiassist.db').resolve().as_posix()}"
    assert Settings(database_url="sqlite:///./krishiassist.db").database_url == expected
    assert Settings(database_url="sqlite:///krishiassist.db").database_url == expected
    assert Settings(database_url="sqlite:///:memory:").database_url == "sqlite:///:memory:"
    assert Settings(database_url="postgresql://u:p@localhost/db").database_url == "postgresql://u:p@localhost/db"


def test_cors_origins_are_read_from_a_comma_separated_setting():
    assert Settings(cors_origins="http://a.example, http://b.example ,").cors_origin_list == ["http://a.example", "http://b.example"]


def test_tests_use_their_own_database_not_the_developers():
    assert "krishiassist_tests_" in str(engine.url)


# ---------- the limiter itself ----------

def test_limiter_blocks_after_the_limit_and_frees_up_when_the_window_passes():
    now = [1000.0]
    limiter = FailureLimiter(max_failures=3, window_seconds=60, clock=lambda: now[0])
    for _ in range(3):
        assert limiter.seconds_until_allowed("a") == 0
        limiter.record("a")
    assert 0 < limiter.seconds_until_allowed("a") <= 60
    assert limiter.seconds_until_allowed("someone-else") == 0      # keys are independent
    with pytest.raises(HTTPException) as blocked:
        limiter.check("a")
    assert blocked.value.status_code == 429 and "Retry-After" in blocked.value.headers
    now[0] += 61
    assert limiter.seconds_until_allowed("a") == 0                 # old failures expired


def test_limiter_reset_forgets_the_failures():
    limiter = FailureLimiter(max_failures=2, window_seconds=60)
    limiter.record("k"); limiter.record("k")
    assert limiter.seconds_until_allowed("k") > 0
    limiter.reset("k")
    assert limiter.seconds_until_allowed("k") == 0


# ---------- sign-in protection through the API ----------

def test_five_wrong_passwords_lock_that_account_even_for_the_right_password():
    email, _ = register()
    for _ in range(5):
        assert login(email, "wrong-password").status_code == 401
    blocked = login(email, PASSWORD)
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0
    assert "try again" in blocked.json()["detail"].lower()


def test_another_account_is_not_affected_by_the_lock():
    locked, _ = register()
    other, _ = register()
    for _ in range(5):
        login(locked, "wrong-password")
    assert login(locked, PASSWORD).status_code == 429
    assert login(other, PASSWORD).status_code == 200


def test_a_successful_sign_in_clears_the_failures_for_that_account():
    email, _ = register()
    for _ in range(3):
        login(email, "wrong-password")
    assert login(email, PASSWORD).status_code == 200
    for _ in range(3):
        assert login(email, "wrong-password").status_code == 401   # not 429: the counter started again


def test_guessing_many_different_emails_from_one_address_is_blocked(monkeypatch):
    monkeypatch.setattr(auth_api, "verify_password", lambda *_: False)   # keep the test fast
    for i in range(20):
        assert login(f"nobody{i}@example.com", "guess").status_code == 401
    assert login("nobody-new@example.com", "guess").status_code == 429


def test_too_many_sign_ups_from_one_address_are_blocked(monkeypatch):
    monkeypatch.setattr(auth_api, "hash_password", lambda _: "not-a-real-hash")   # keep the test fast
    for i in range(10):
        assert client.post("/api/auth/register", json={"name": "Bulk User", "email": f"bulk{i}-{uuid.uuid4().hex[:6]}@example.com", "password": PASSWORD}).status_code == 200
    assert client.post("/api/auth/register", json={"name": "Bulk User", "email": "one-too-many@example.com", "password": PASSWORD}).status_code == 429


def test_unknown_email_still_costs_one_password_check_so_timing_does_not_leak(monkeypatch):
    calls = []
    real = auth_api.verify_password
    monkeypatch.setattr(auth_api, "verify_password", lambda *a: calls.append(a) or real(*a))
    assert login("nobody-here@example.com", "whatever123").status_code == 401
    assert len(calls) == 1


# ---------- tokens ----------

def _token(payload, secret=None):
    return jwt.encode(payload, secret or settings.jwt_secret, algorithm=settings.jwt_algorithm)


def test_good_token_works_and_bad_tokens_are_refused():
    _, headers = register()
    assert client.get("/api/profile", headers=headers).status_code == 200
    user_id = client.get("/api/profile", headers=headers).json()["user_id"]
    soon = datetime.now(timezone.utc) + timedelta(minutes=5)
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    bad = {
        "no expiry date": _token({"sub": str(user_id)}),
        "expired": _token({"sub": str(user_id), "exp": past}),
        "signed with another secret": _token({"sub": str(user_id), "exp": soon}, secret="another-secret-another-secret-123456"),
        "no subject": _token({"exp": soon}),
    }
    for reason, token in bad.items():
        assert client.get("/api/profile", headers={"Authorization": f"Bearer {token}"}).status_code == 401, reason
