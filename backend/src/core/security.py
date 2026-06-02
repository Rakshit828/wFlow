from cryptography.fernet import Fernet
from src.config import CONFIG
from beanie import PydanticObjectId
from datetime import datetime, timezone
import jwt
import uuid
from loguru import logger

from src.utils.utils import REFRESH_TOKEN_EXPIRY, ACCESS_TOKEN_EXPIRY
from src.config import CONFIG

cipher_suite = Fernet(CONFIG.ENCRYPTION_KEY)


def encrypt_token(token: str | None) -> str | None:
    if not token:
        return None
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(token_enc: str | None) -> str | None:
    if not token_enc:
        return None
    return cipher_suite.decrypt(token_enc.encode()).decode()


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



