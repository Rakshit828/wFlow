from src.repositories.auth_repository import UserRepository, OAuthAccountRepository
from src.integrations.googlecould import GoogleOAuthInterface, GoogleAuthResponse
from src.db.models import Users
from src.core.exceptions import AppError
from src.core.security import create_jwt_tokens
from src.utils.utils import set_cookies
from src.db.redis import Redis
from src.schemas.auth_schemas import LoginResponse
from fastapi import Response


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
            # Create rows only if the user doesn't exist.
            user: Users | None = await self.user_repo.create_user(
                email=auth_response.decoded_id_token.email,
                name=auth_response.decoded_id_token.name,
                username=None,
                avatar_url=str(auth_response.decoded_id_token.picture),
                is_verified=auth_response.decoded_id_token.email_verified,
            )

            if user is None:
                raise AppError()

            await self.oauth_repo.create_oauth_account(
                user_ref=user.id,
                provider="google",
                provider_email=auth_response.decoded_id_token.email,
                is_email_verified=auth_response.decoded_id_token.email_verified,
                scopes=auth_response.scopes,
                provider_sub_id=auth_response.decoded_id_token.sub,
                access_token=auth_response.access_token,
                refresh_token=auth_response.refresh_token,
                access_token_expiry=auth_response.expires_in,
                refresh_token_expiry=None,
            )

        tokens = await create_jwt_tokens(user.id, is_login=True)

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


