from src.domains.users.repository import (
    UserRepository,
    OAuthAccountRepository,
    SessionRepository,
)
from src.integrations.services.Google import GoogleOAuthInterface, GoogleAuthResponse
from src.utils.utils import set_cookie
from src.db.redis import Redis
from src.core.response import AppError
from src.db.postgres.schemas import Users, OAuthAccounts, LoginProvidersEnum, Session
from src.config import CONFIG
from src.core.security import hash_session_token
from src.utils.utils import parse_expiry
from src.integrations.services.Google.scopes import GOOGLE_OPENID_SCOPE

import secrets
from loguru import logger
from fastapi import Response
from datetime import timedelta, datetime
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.domains._shared.constants import SESSION_COOKIE_NAME


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.session_repo = SessionRepository()
        self.oauth_repo = OAuthAccountRepository()
        self.google_oauth = GoogleOAuthInterface()

    async def google_login_url(self, redis: Redis, login_redirect: bool = True) -> str:
        url = await self.google_oauth.create_authorization_url(
            db=redis,
            login_redirect=login_redirect,
            scopes_requested=GOOGLE_OPENID_SCOPE,
        )
        return url

    async def google_login_callback(
        self,
        session: AsyncSession,
        *,
        code: str,
        state: str,
        response: Response,
        redis: Redis,
    ):
        tokens: dict[str, str] = await self.google_oauth.exchange_for_code(
            db=redis, code=code, state=state
        )
        auth_response: GoogleAuthResponse = (
            await self.google_oauth.get_openid_auth_payload(tokens)
        )

        user: Users | None = await self.user_repo.get_user_by_email(
            session=session, email=auth_response.decoded_id_token.email
        )

        if not user:
            user: Users = Users(
                email=auth_response.decoded_id_token.email,
                full_name=auth_response.decoded_id_token.name,
                username=auth_response.decoded_id_token.email.split("@")[0],
                avatar_url=str(auth_response.decoded_id_token.picture),
                email_verified=auth_response.decoded_id_token.email_verified,
            )
            new_user: Users | None = await self.user_repo.create_user(session, user)

            if new_user is None:
                raise AppError()
            user = new_user

            oauth_acc = OAuthAccounts(
                user_id=new_user.id,
                provider=LoginProvidersEnum.GOOGLE,
                provider_email=auth_response.decoded_id_token.email,
                provider_sub_id=auth_response.decoded_id_token.sub,
            )
            oauth_acc = await self.oauth_repo.create_oauthaccount(
                session=session, oauth_acc=oauth_acc
            )

            if oauth_acc is None:
                raise AppError()

        token = secrets.token_urlsafe(32)
        token_expiry: timedelta = parse_expiry(CONFIG.SESSION_TOKEN_EXPIRY)
        set_cookie(
            response=response, key=SESSION_COOKIE_NAME, value=token, expiry=token_expiry
        )

        new_session = Session(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=datetime.now() + token_expiry,
        )
        await self.session_repo.create_session(session, new_session)

        # return RedirectResponse("http://localhost:8000/docs")
