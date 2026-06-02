from src.repositories.auth_repository import UserRepository, OAuthAccountRepository
from src.integrations.googlecloud import GoogleOAuthInterface, GoogleAuthResponse
from src.db.models import Users, OAuthAccounts
from src.core.exceptions import AppError
from src.core.security import create_jwt_tokens
from src.utils.utils import set_cookies
from src.db.redis import Redis
from src.schemas.auth_schemas import LoginResponse
from fastapi import Response
from fastapi.responses import RedirectResponse
from src.core.security import encrypt_token
from datetime import timedelta, datetime, timezone
from loguru import logger


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.oauth_repo = OAuthAccountRepository()
        self.google_oauth = GoogleOAuthInterface()

    async def google_login_callback(
        self, code: str, state: str, response: Response, redis: Redis
    ) -> LoginResponse:
        tokens: dict[str, str] = await self.google_oauth.exchange_for_code(
            db=redis, code=code, state=state
        )
        auth_response: GoogleAuthResponse = (
            await self.google_oauth.get_openid_auth_payload(tokens)
        )

        user = await self.user_repo.get_user_by_email(
            auth_response.decoded_id_token.email
        )

        if not user:
            user: Users = Users(
                email=auth_response.decoded_id_token.email,
                full_name=auth_response.decoded_id_token.name,
                username=auth_response.decoded_id_token.email.split("@")[0],
                avatar_url=str(auth_response.decoded_id_token.picture),
                is_verified=auth_response.decoded_id_token.email_verified,
            )
            new_user: Users | None = await self.user_repo.create_user(user)

            if new_user is None:
                raise AppError()

            access_token_enc = encrypt_token(auth_response.access_token)
            refresh_token_enc = encrypt_token(auth_response.refresh_token)
            now = datetime.now(timezone.utc)
            refresh_token_expiry = None
            access_token_expiry = now + timedelta(seconds=auth_response.expires_in)

            oauth_acc = OAuthAccounts(
                user=user.id,
                provider="google",
                provider_email=auth_response.decoded_id_token.email,
                provider_sub_id=auth_response.decoded_id_token.sub,
                is_email_verified=auth_response.decoded_id_token.email_verified,
                scopes=auth_response.scopes if auth_response.scopes else [],
                access_token_enc=access_token_enc,
                refresh_token_enc=refresh_token_enc,
                access_token_expiry=access_token_expiry,
                refresh_token_expiry=refresh_token_expiry,
            )
            oauth_acc = await self.oauth_repo.create_oauth_account(oauth_account=oauth_acc)

            if oauth_acc is None:
                raise AppError()


        tokens = await create_jwt_tokens(user.id, is_login=True)
        logger.info(f"Tokens are : {tokens}")
        set_cookies(
            response=response,
            tokens={
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
            },
        )

        return LoginResponse(
            user_id=user.id,
            email=user.email,
            created_at=user.created_at,
        )

        # return RedirectResponse("http://localhost:8000/docs")
