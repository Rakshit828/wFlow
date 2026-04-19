import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import get_settings
from app.models.user import User, RefreshToken

settings = get_settings()

def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": [r.name for r in user.roles],
        "permissions": list({
            f"{p.resource}:{p.action}"
            for r in user.roles
            for p in r.permissions
        }),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

async def create_refresh_token(db: AsyncSession, user: User, family: str | None = None) -> str:
    raw_token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token_family = family or secrets.token_urlsafe(16)

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        family=token_family,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh)
    await db.flush()
    return raw_token  # Return raw — hash stored in DB

async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> tuple[User, str]:
    """Detect reuse attacks (revoke whole family), issue new token."""
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if not stored:
        raise ValueError("Refresh token not found")

    if stored.is_revoked or stored.expires_at < datetime.now(timezone.utc):
        # Reuse detected — revoke entire family (token rotation attack mitigation)
        if stored.is_revoked:
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.family == stored.family)
                .values(is_revoked=True)
            )
        raise ValueError("Refresh token is invalid or expired")

    # Revoke used token
    stored.is_revoked = True
    await db.flush()

    # Load user and issue new token in same family
    result = await db.execute(select(User).where(User.id == stored.user_id))
    user = result.scalar_one()

    new_raw = await create_refresh_token(db, user, family=stored.family)
    return user, new_raw

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])