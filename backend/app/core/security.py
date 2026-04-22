"""
AdTicks — Security utilities.

Provides:
- hash_password / verify_password (bcrypt via passlib)
- create_access_token (JWT via python-jose)
- get_current_user  FastAPI dependency
- Token blacklist for logout
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT Token Blacklist (Redis-backed)
# ---------------------------------------------------------------------------
async def get_redis():
    """Get Redis client for token blacklisting."""
    import redis.asyncio as redis
    
    return await redis.from_url(settings.REDIS_URL, decode_responses=True)


async def revoke_token(token: str) -> None:
    """Add token to blacklist with expiry based on token's exp claim."""
    try:
        redis_client = await get_redis()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        
        if exp:
            # Calculate TTL from token expiry
            now = datetime.now(tz=timezone.utc).timestamp()
            ttl = max(0, int(exp - now))
            if ttl > 0:
                await redis_client.setex(f"blacklist:{token}", ttl, "revoked")
        await redis_client.aclose()
    except Exception as e:
        logger.error("token_revoke_failed", extra={"error": str(e)})


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    try:
        redis_client = await get_redis()
        is_blacklisted = await redis_client.exists(f"blacklist:{token}")
        await redis_client.aclose()
        return bool(is_blacklisted)
    except Exception as e:
        logger.error("blacklist_check_failed", extra={"error": str(e)})
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT.

    Parameters
    ----------
    subject:
        Typically the user's UUID (will be cast to str).
    expires_delta:
        Override the default expiry window from settings.
    extra_claims:
        Additional claims to embed in the token payload.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | UUID) -> str:
    """
    Create a long-lived refresh token (7 days).
    
    Parameters
    ----------
    subject:
        The user's UUID.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(days=7)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Current-user dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Decode the Bearer JWT and return the corresponding User ORM object.

    Raises HTTP 401 if the token is invalid, blacklisted, or the user doesn't exist.
    """
    # Import here to avoid circular imports at module load time
    from app.models.user import User  # noqa: PLC0415

    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        logger.warning("access_attempt_blacklisted_token")
        raise AuthenticationError("Token has been revoked. Please log in again.")

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise AuthenticationError()
    except JWTError as e:
        logger.warning("jwt_validation_failed", extra={"error": str(e)})
        raise AuthenticationError()

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("user_not_found", extra={"user_id": user_id})
        raise AuthenticationError()
    if not user.is_active:
        logger.warning("inactive_user_access_attempt", extra={"user_id": str(user.id)})
        raise AuthenticationError("Account is inactive")
    return user


def verify_refresh_token(token: str) -> UUID:
    """
    Verify a refresh token and return the user ID.
    
    Raises AuthenticationError if the token is invalid or not a refresh token.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise AuthenticationError("Invalid refresh token")
        return UUID(user_id)
    except (JWTError, ValueError) as e:
        logger.warning("refresh_token_invalid", extra={"error": str(e)})
        raise AuthenticationError("Invalid refresh token")

