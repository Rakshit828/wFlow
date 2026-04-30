"""Contains the github specific login and authorization and OAuth2.0.."""

import secrets
import httpx
from loguru import logger

from src.integrations.oauth2 import OAuthInterface
from src.config import CONFIG
from src.db.redis import Redis


class GitHubOAuthInterface(OAuthInterface):
    PROVIDER = "GITHUB"

    def __init__(self):
        super().__init__()
        self.async_client = httpx.AsyncClient(headers={"Accept": "application/json"})

    async def create_authorization_url(
        self,
        db: Redis,
        login_redirect: bool,
        scopes_requested: list[str] | None = None,
    ):
        # Default scope to 'read:user' and 'user:email'
        scopes = (
            " ".join(scopes_requested) if scopes_requested else "read:user user:email"
        )

        state = secrets.token_urlsafe(32)
        # Note: GitHub doesn't strictly use PKCE, but we keep it for interface parity
        code_verifier, code_challenge = self._generate_pkce_pair()

        # Store state and verifier in Redis
        await db.set(f"oauth:github:{state}", code_verifier, ex=5 * 60)

        params = {
            "client_id": CONFIG.GITHUB_CLIENT_ID,
            "redirect_uri": (
                CONFIG.GITHUB_LOGIN_REDIRECT_URL
                if login_redirect
                else CONFIG.GITHUB_SCOPE_REDIRECT_URL
            ),
            "scope": scopes,
            "state": state,
            "allow_signup": "true",
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{CONFIG.GITHUB_AUTH_URL}?{query_string}"
        return url

    async def exchange_for_code(
        self, db: Redis, code: str, state: str
    ) -> dict[str, str]:

        redis_key = f"oauth:github:{state}"
        stored_verifier = await db.get(redis_key)

        if not stored_verifier:
            raise Exception("Session Expired or State Mismatch")

        await db.delete(redis_key)

        data = {
            "client_id": CONFIG.GITHUB_CLIENT_ID,
            "client_secret": CONFIG.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": CONFIG.GITHUB_LOGIN_REDIRECT_URL,
        }

        response = await self.async_client.post(CONFIG.GITHUB_TOKEN_URL, data=data)

        if response.status_code != 200:
            logger.error(f"GitHub exchange failed: {response.text}")
            raise Exception(f"GitHub token exchange failed")

        return (
            response.json()
        )  # Returns {'access_token': '...', 'token_type': 'bearer', 'scope': '...'}


    async def get_user_profile(self, access_token: str) -> dict:
        """
        Since GitHub doesn't provide an ID Token, we manually fetch the user profile.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "",  # GitHub requires a User-Agent
        }

        response = await self.async_client.get(
            CONFIG.GITHUB_GET_PROFILE_URL, headers=headers
        )

        if response.status_code != 200:
            raise Exception("Failed to fetch GitHub user profile")

        return response.json()
