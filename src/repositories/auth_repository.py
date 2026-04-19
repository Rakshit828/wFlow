from src.db.postgres.schemas import User, AppIntegrationsCredentials, OAuthAccounts
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timezone, timedelta

from src.services.encryption import encrypt_token
from src.integrations.googlecould.types import GoogleAuthResponse


class UserRepository:
    async def get_user_by_id(self, session: AsyncSession, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result: User = (await session.execute(stmt)).scalar_one_or_none()
        return result

    async def get_user_by_email(self, session: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result: User = (await session.execute(stmt)).scalar_one_or_none()
        return result

    async def create_user(
        self,
        session: AsyncSession,
        email: str,
        name: str | None,
        avatar_url: str,
        is_verified: str,
    ) -> User:
        user = User(
            email=email, name=name, avatar_url=avatar_url, is_verified=is_verified
        )
        session.add(user)
        await session.flush()
        return user


class AppIntegrationsCredentialsRepository:
    async def create_integration(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        provider: str,
        access_token: str,
        refresh_token: str | None,
        scopes: list[str],
        token_type: str,
        access_token_expires_in: int,
    ) -> AppIntegrationsCredentials:

        access_token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=access_token_expires_in
        )

        integration = AppIntegrationsCredentials(
            user_id=user_id,
            provider=provider,
            access_token_enc=encrypt_token(access_token),
            refresh_token_enc=encrypt_token(refresh_token),
            scopes=scopes,
            access_token_expiry=access_token_expiry,
            token_type=token_type,
        )
        session.add(integration)
        await session.flush()
        return integration


class OAuthAccountsRepository:
    async def create_oauth_account(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        integration_id: uuid.UUID,
        provider: str,
        auth_response: GoogleAuthResponse,
    ) -> OAuthAccounts:
        payload = auth_response.decoded_id_token
        oauth_account = OAuthAccounts(
            user_id=user_id,
            integration_id=integration_id,
            provider=provider,
            provider_sub=payload.sub,
            provider_email=payload.email,
            is_email_verified=payload.email_verified,
        )
        session.add(oauth_account)
        await session.flush()
        return oauth_account
