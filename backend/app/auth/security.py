from datetime import datetime, timedelta, timezone
import hashlib, hmac, secrets
from functools import lru_cache
import jwt
from app.core.config import settings

ITERATIONS = 310_000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = encoded.split('$')
        if scheme != 'pbkdf2_sha256': return False
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError): return False

@lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    """A throw-away hash. Checking a password against it when the e-mail is unknown makes
    'unknown e-mail' take as long as 'wrong password', so response time does not reveal
    which e-mail addresses have accounts."""
    return hash_password(secrets.token_urlsafe(16))

def create_access_token(user_id: int, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({'sub': str(user_id), 'role': role, 'exp': exp}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    # 'exp' and 'sub' are mandatory: a token without an expiry date would never stop working.
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={'require': ['exp', 'sub']})
