"""Contains the google specific login for OAuth 2.0 and OpenID Connect(OIDC)."""

import secrets
from loguru import logger
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from fastapi.concurrency import run_in_threadpool
import httpx

from src.integrations.oauth2 import OAuthInterface
from src.config import CONFIG
from src.db.redis import Redis


class GoogleOAuthInterface(OAuthInterface):
    PROVIDER = "GOOGLE"

    def __init__(self):
        super().__init__()
        self.async_client = httpx.AsyncClient()

    async def verify_oauth2_token_async(self, id_token_str: str):
        try:
            # We run the sync library in a threadpool to remain 'async'
            id_info = await run_in_threadpool(
                id_token.verify_oauth2_token,
                id_token_str,
                google_requests.Request(),
                CONFIG.GOOGLE_CLIENT_ID,
            )
            return id_info

        except Exception as e:
            logger.error(f"Google Token Verification Failed: {e}")
            raise ValueError(f"Invalid Token: {str(e)}")

    async def create_authorization_url(
        self, db: Redis, scopes_requested: str | list[str]
    ):
        if isinstance(scopes_requested, list):
            scopes = " ".join(scopes_requested)
        elif isinstance(scopes_requested, str):
            scopes = scopes_requested
        else:
            raise TypeError("Invalid Type for parameter, scopes_requested=")

        state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = self._generate_pkce_pair()

        await db.set(f"oauth:{state}", code_verifier, ex=5 * 60)

        params = {
            "client_id": CONFIG.GOOGLE_CLIENT_ID,
            "response_type": "code",
            "scope": scopes,
            "redirect_uri": CONFIG.GOOGLE_REDIRECT_URL,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        url = f"{CONFIG.GOOGLE_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return url


    async def exchange_for_code(self, db: Redis, code: str, state: str) -> dict:

        redis_key = f"oauth:{state}"
        stored_verifier = await db.get(redis_key)
        if not stored_verifier:
            raise Exception("Session Expired or State Mismatch")
        await db.delete(redis_key)

        data = {
            "code": code,
            "client_id": CONFIG.GOOGLE_CLIENT_ID,
            "client_secret": CONFIG.GOOGLE_CLIENT_SECRET,
            "code_verifier": stored_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": CONFIG.GOOGLE_REDIRECT_URL,
        }

        async with self.async_client as client:
            response = await client.post(CONFIG.GOOGLE_TOKEN_URL, data=data)

        if response.status_code != 200:
            raise Exception(f"Google token exchange failed: {response.text}")

        tokens = response.json()

        profile_info = await self.verify_oauth2_token_async(tokens.get("id_token"))

        return {
            "access_token": tokens.get("access_token"),
            "profile_info": profile_info,
            "refresh_token": tokens.get("refresh_token"),
        }
