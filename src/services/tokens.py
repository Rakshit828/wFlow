from beanie import PydanticObjectId
from datetime import datetime, timezone, timedelta
import jwt
import uuid
from loguru import logger
from src.config import CONFIG
from fastapi import Response

# Helper functions
def _parse_expiry(raw: str) -> timedelta:
    """Convert human-friendly expiry strings to timedelta.

    Supports: 30s, 15m, 1h, 7d
    """
    raw = raw.strip().lower()
    unit = raw[-1]
    value = int(raw[:-1])
    mapping = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    if unit not in mapping:
        raise ValueError(
            f"Unsupported expiry unit '{unit}'. Use one of: {list(mapping.keys())}"
        )
    return timedelta(**{mapping[unit]: value})



ACCESS_TOKEN_EXPIRY = _parse_expiry(CONFIG.ACCESS_TOKEN_EXPIRY)
REFRESH_TOKEN_EXPIRY = _parse_expiry(CONFIG.REFRESH_TOKEN_EXPIRY)



async def create_jwt_tokens(
    user_id: PydanticObjectId, is_login: bool
) -> dict:
    """
        This function is used to create both access and refresh token:
        
        For both tokens:
        ```python
        tokens = await create_jwt_tokens(user_id, role, is_login = True)
        ```
    
        For access token: 
        ```python
        access_token = await create_jwt_tokens(user_id, role, is_login = False)
        ```
    """
    now = datetime.now(timezone.utc)
    

    access_payload = {
        "jti": str(uuid.uuid4()),
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRY,
    }
    access_token = jwt.encode(
        payload=access_payload,
        key=CONFIG.JWT_SECRET_KEY,
        algorithm=CONFIG.JWT_ALGORITHM,
    )

    if is_login:
        refresh_payload = {
            "jti": str(uuid.uuid4()),
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": now + REFRESH_TOKEN_EXPIRY,
        }
        refresh_token = jwt.encode(
            payload=refresh_payload,
            key=CONFIG.JWT_SECRET_KEY,
            algorithm=CONFIG.JWT_ALGORITHM,
        )
    
    if is_login is True:
        return {"access_token": access_token, "refresh_token": refresh_token}
    else:
        return { "access_token": access_token }
    


def decode_jwt_tokens(jwt_token: str) -> str:
    try:
        decoded_jwt = jwt.decode(
            jwt=jwt_token,
            key=CONFIG.JWT_SECRET_KEY,
            algorithms=[CONFIG.JWT_ALGORITHM],
        )
        return decoded_jwt

    except jwt.ExpiredSignatureError:
        logger.error("JWT Signature expired.")
        pass
    except jwt.InvalidTokenError:
        logger.error("Invalid JWT Error.")
        pass


def set_cookies(response: Response, tokens: dict[str, str]):
    """Set JWT tokens as HTTP-only cookies in the response."""
    
    # Set access token cookie
    if "access_token" in tokens:
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            max_age=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
            httponly=True,
            secure=CONFIG.ENVIRONMENT == "production",
            samesite="none",
            path="/",
        )
    
    # Set refresh token cookie if present
    if "refresh_token" in tokens:
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            max_age=int(REFRESH_TOKEN_EXPIRY.total_seconds()),
            httponly=True,
            secure=CONFIG.ENVIRONMENT == "production",
            samesite="none",
            path="/",
        )