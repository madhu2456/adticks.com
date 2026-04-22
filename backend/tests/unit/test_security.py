"""Unit tests for app.core.security: hash_password, verify_password, create_access_token."""
import uuid
from datetime import timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password


# ---------------------------------------------------------------------------
# hash_password
# ---------------------------------------------------------------------------

def test_hash_password_returns_different_string_from_input():
    """hash_password output is not equal to the plain-text input."""
    plain = "my-secret-password"
    hashed = hash_password(plain)
    assert hashed != plain


def test_hash_password_returns_string():
    """hash_password returns a string."""
    result = hash_password("password123")
    assert isinstance(result, str)


def test_hash_password_is_not_deterministic():
    """Two hashes of the same password differ (bcrypt uses random salt)."""
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2


def test_hash_password_starts_with_bcrypt_prefix():
    """Bcrypt hashes start with the $2b$ identifier."""
    hashed = hash_password("testpass")
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


# ---------------------------------------------------------------------------
# verify_password
# ---------------------------------------------------------------------------

def test_verify_password_correct_password_returns_true():
    """verify_password returns True when the plain password matches the hash."""
    plain = "correct-horse-battery-staple"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong_password_returns_false():
    """verify_password returns False when the plain password does not match."""
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_empty_string_returns_false():
    """verify_password returns False for an empty string against a real hash."""
    hashed = hash_password("not-empty")
    assert verify_password("", hashed) is False


def test_verify_password_case_sensitive():
    """Passwords are case-sensitive; wrong case returns False."""
    hashed = hash_password("Password123")
    assert verify_password("password123", hashed) is False


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

def test_create_access_token_with_uuid_subject():
    """Token sub claim equals the str representation of the UUID."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == str(user_id)


def test_create_access_token_with_string_subject():
    """Token sub claim equals the string subject passed in."""
    token = create_access_token(subject="user-123")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "user-123"


def test_create_access_token_has_exp_claim():
    """Token payload contains an exp (expiry) claim."""
    token = create_access_token(subject="test")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert "exp" in payload


def test_create_access_token_has_iat_claim():
    """Token payload contains an iat (issued at) claim."""
    token = create_access_token(subject="test")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert "iat" in payload


def test_create_access_token_decodes_with_correct_secret():
    """Token created with settings.SECRET_KEY decodes successfully."""
    token = create_access_token(subject="some-user")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload is not None


def test_create_access_token_fails_with_wrong_secret():
    """Token cannot be decoded with a different secret key."""
    from jose import JWTError
    token = create_access_token(subject="user-x")
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong-secret", algorithms=[settings.ALGORITHM])


def test_create_access_token_custom_expires_delta():
    """custom expires_delta is reflected in the exp claim."""
    import time
    delta = timedelta(seconds=60)
    before = int(time.time())
    token = create_access_token(subject="user-y", expires_delta=delta)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    exp = payload["exp"]
    # exp should be roughly before + 60
    assert before + 55 <= exp <= before + 65


def test_create_access_token_extra_claims_embedded():
    """Extra claims passed via extra_claims appear in the payload."""
    token = create_access_token(
        subject="user-z",
        extra_claims={"role": "admin", "plan": "pro"},
    )
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["role"] == "admin"
    assert payload["plan"] == "pro"


def test_create_access_token_returns_string():
    """create_access_token returns a non-empty string."""
    token = create_access_token(subject="abc")
    assert isinstance(token, str)
    assert len(token) > 0
