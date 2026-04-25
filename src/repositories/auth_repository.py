import uuid
from datetime import datetime, timezone, timedelta
from loguru import logger
from beanie import PydanticObjectId

from src.core.security import encrypt_token
from src.integrations.googlecould.types import GoogleAuthResponse
from src.db.models import Users, AppIntegrations, OAuthAccounts


class UserRepository:
    async def get_user_by_id(self, user_id: str) -> Users | None:
        user = await Users.find_one(Users.id == PydanticObjectId(user_id))
        return user

    async def get_user_by_email(self, email: str) -> Users | None:
        user = await Users.find_one(Users.email == email)
        return user

    async def create_user(self, user: Users) -> Users | None:
        created_user = await Users.insert(user)
        return created_user


class OAuthAccountRepository:
    async def create_oauth_account(
        self, oauth_account: OAuthAccounts
    ) -> OAuthAccounts | None:
        created_oauth_account = await OAuthAccounts.insert_one(oauth_account)
        return created_oauth_account
