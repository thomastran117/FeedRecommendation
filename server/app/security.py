import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings
from app.redis_client import get_redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_REFRESH_KEY_PREFIX = "refresh_token:"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


async def create_refresh_token(user_id: str) -> str:
    jti = str(uuid.uuid4())
    expires = timedelta(days=settings.refresh_token_expire_days)
    token = _create_token({"sub": user_id, "type": "refresh", "jti": jti}, expires)

    redis = get_redis()
    await redis.setex(
        f"{_REFRESH_KEY_PREFIX}{jti}",
        int(expires.total_seconds()),
        user_id,
    )

    return token


async def rotate_refresh_token(token: str) -> tuple[str, str]:
    """Validate a refresh token, revoke it, and issue a new pair."""
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise ValueError("Not a refresh token")

    jti = payload.get("jti")
    user_id = payload.get("sub")

    redis = get_redis()
    stored = await redis.getdel(f"{_REFRESH_KEY_PREFIX}{jti}")

    if stored is None:
        raise ValueError("Refresh token not found or already used")

    return create_access_token(user_id), await create_refresh_token(user_id)


async def revoke_refresh_token(token: str) -> None:
    """Revoke a single refresh token (e.g. on logout)."""
    payload = decode_token(token)
    jti = payload.get("jti")
    if jti:
        redis = get_redis()
        await redis.delete(f"{_REFRESH_KEY_PREFIX}{jti}")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
