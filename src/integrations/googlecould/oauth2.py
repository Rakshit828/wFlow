"""Contains the google specific login for OAuth 2.0 and OpenID Connect(OIDC)."""

import secrets
from loguru import logger
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from fastapi.concurrency import run_in_threadpool
import httpx
from typing import Literal

from src.integrations.oauth2 import OAuthInterface
from src.config import CONFIG
from src.db.redis import Redis
from src.integrations.googlecould.types import (
    GoogleAuthResponse,
    GoogleIDTokenPayload,
    GoogleNewScopeResponse,
    GoogleIDTokenPayloadOnlyEmail,
)
from src.integrations.googlecould.scopes import (
    GOOGLE_SCOPES,
    GOOGLE_OPENID_SCOPE,
    GOOGLE_EMAIL_ONLY_OPENID_SCOPE,
    get_scopes,
)


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
        self,
        db: Redis,
        login_redirect: bool,
        scopes_requested: list[str] | None = None,
        prompt: Literal["none", "consent", "select_account", None] = "consent",
    ):
        scopes = GOOGLE_OPENID_SCOPE if not scopes_requested else " ".join(scopes_requested)
        
        state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = self._generate_pkce_pair()

        await db.set(f"oauth:{state}", code_verifier, ex=5 * 60)

        params = {
            "client_id": CONFIG.GOOGLE_CLIENT_ID,
            "response_type": "code",
            "scope": scopes,
            "redirect_uri": (
                CONFIG.GOOGLE_LOGIN_REDIRECT_URL
                if login_redirect
                else CONFIG.GOOGLE_SCOPE_REDIRECT_URL
            ),
            "state": state,
            "access_type": "offline",
            "code_challenge": code_challenge,
            "prompt": prompt,
            "code_challenge_method": "S256",
        }

        url = f"{CONFIG.GOOGLE_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return url


    async def exchange_for_code_new_authorization(
        self, db: Redis, code: str, state: str
    ) -> dict[str, str]:

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
            "redirect_uri": CONFIG.GOOGLE_SCOPE_REDIRECT_URL,
        }

        response = await self.async_client.post(CONFIG.GOOGLE_TOKEN_URL, data=data)

        if response.status_code != 200:
            raise Exception(f"Google token exchange failed: {response.text}")

        tokens = response.json()
        return tokens

    async def exchange_for_code(
        self, db: Redis, code: str, state: str
    ) -> dict[str, str]:

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
            "redirect_uri": CONFIG.GOOGLE_LOGIN_REDIRECT_URL,
        }

        response = await self.async_client.post(CONFIG.GOOGLE_TOKEN_URL, data=data)

        if response.status_code != 200:
            raise Exception(f"Google token exchange failed: {response.text}")

        tokens = response.json()
        return tokens

    async def get_openid_auth_payload(self, tokens: dict[str, str]):
        logger.info(f"Tokens response is : {tokens}")

        profile_info = await self.verify_oauth2_token_async(tokens.get("id_token"))
        profile_info = GoogleIDTokenPayload(**profile_info)

        return GoogleAuthResponse(**tokens, decoded_id_token=profile_info)

    async def get_openid_payload_new_authorization(
        self, tokens: dict[str, str]
    ) -> GoogleNewScopeResponse:
        logger.info(f"Tokens are : {tokens}")
        decoded_jwt = await self.verify_oauth2_token_async(tokens.get("id_token"))
        decoded_jwt = GoogleIDTokenPayloadOnlyEmail(**decoded_jwt)
        return GoogleNewScopeResponse(**tokens, decoded_id_token=decoded_jwt)
