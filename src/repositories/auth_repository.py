import uuid
from datetime import datetime, timezone, timedelta
from loguru import logger
from beanie import PydanticObjectId

from src.services.encryption import encrypt_token
from src.integrations.googlecould.types import GoogleAuthResponse
from src.db.mongo.schemas import Users, AppIntegrations, OAuthAccounts


class UserRepository:
    async def get_user_by_id(self, user_id: str) -> Users | None:
        user = await Users.find_one(Users.id == PydanticObjectId(user_id))
        return user

    async def get_user_by_email(self, email: str) -> Users | None:
        user = await Users.find_one(Users.email == email)
        return user

    async def create_user(
        self,
        email: str,
        name: str | None,
        username: str | None,
        avatar_url: str,
        is_verified: bool,
    ) -> Users | None:
        created_user = await Users.insert_one(
            Users(
                email=email,
                full_name=name,
                username=username,
                avatar_url=avatar_url,
                is_email_verified=is_verified,
            )
        )
        return created_user


class OAuthAccountRepository:
    async def create_oauth_account(
        self,
        user_ref: str,
        provider: str,
        provider_email: str,
        provider_sub_id: str,
        access_token: str,
        access_token_expiry: datetime,
        is_email_verified: bool = False,
        scopes: list[str] | None = None,
        refresh_token: str | None = None,
        refresh_token_expiry: datetime | None = None,
    ) -> OAuthAccounts | None:
        if scopes is None:
            scopes = []
        
        encrypted_access_token = encrypt_token(access_token)
        encrypted_refresh_token = encrypt_token(refresh_token) if refresh_token else None
        
        user = await Users.find_one(Users.id == user_ref)

        if not user:
            logger.error(f"User with id {user_ref} not found")
            return None
        
        created_oauth_account = await OAuthAccounts.insert_one(
            OAuthAccounts(
                user=user,
                provider=provider,
                provider_email=provider_email,
                provider_sub_id=provider_sub_id,
                is_email_verified=is_email_verified,
                scopes=scopes,
                access_token_enc=encrypted_access_token,
                access_token_expiry=access_token_expiry,
                refresh_token_enc=encrypted_refresh_token,
                refresh_token_expiry=refresh_token_expiry,
            )
        )
        return created_oauth_account