"""AES encryption (via cryptography.fernet)"""

from cryptography.fernet import Fernet
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