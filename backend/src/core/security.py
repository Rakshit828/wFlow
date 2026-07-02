from cryptography.fernet import Fernet
import hashlib
from src.config import CONFIG

from src.config import CONFIG

cipher_suite = Fernet(CONFIG.ENCRYPTION_KEY)


def encrypt_payload(payload: str) -> str:
    return cipher_suite.encrypt(payload.encode()).decode()


def decrypt_payload(payload_enc: str) -> str:
    return cipher_suite.decrypt(payload_enc.encode()).decode()


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
