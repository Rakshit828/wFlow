import secrets
import hashlib
import base64
from abc import ABC, abstractmethod



class OAuthInterface(ABC):
    def __init__(self):
        pass

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Returns (code_verifier, code_challenge) for PKCE."""
        code_verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return code_verifier, code_challenge
    
    @abstractmethod
    async def create_authorization_url(self) -> str:
        pass

    @abstractmethod
    async def exchange_for_code(self) -> dict:
        pass

