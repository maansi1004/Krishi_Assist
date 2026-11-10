"""Shared test setup. Runs before any test file is imported.

* Every test run gets its OWN temporary database, so tests can never fill (or read)
  the database you use while developing.
* The sign-in limits are fixed to their default values, whatever your .env says.
* Rate-limit counters are cleared before each test, so tests do not block each other.
"""
import atexit
import os
import shutil
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="krishiassist_tests_")
atexit.register(shutil.rmtree, _tmp, ignore_errors=True)

os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp, 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(Path(_tmp, "uploads").as_posix())
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "test-secret-for-the-test-suite-only-0123456789"
os.environ["LOGIN_MAX_FAILURES"] = "5"
os.environ["LOGIN_MAX_FAILURES_PER_IP"] = "20"
os.environ["LOGIN_WINDOW_MINUTES"] = "15"
os.environ["REGISTER_MAX_PER_HOUR"] = "10"
os.environ["MAX_UPLOAD_MB"] = "5"
os.environ["MAX_DOCUMENTS_PER_USER"] = "25"
os.environ["MAX_STORAGE_MB_PER_USER"] = "50"
os.environ["UPLOAD_MAX_PER_HOUR"] = "30"

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_rate_limits():
    from app.services.rate_limit import ALL_LIMITERS

    for limiter in ALL_LIMITERS:
        limiter.clear()
    yield


@pytest.fixture(autouse=True)
def clean_scheme_overrides():
    """Administrator decisions are stored in the database and cached in memory; start every test clean."""
    yield
    from app.db.session import SessionLocal
    from app.models.scheme_override import SchemeOverride
    from app.services.scheme_service import set_overrides

    db = SessionLocal()
    try:
        db.query(SchemeOverride).delete()
        db.commit()
    finally:
        db.close()
    set_overrides({})
