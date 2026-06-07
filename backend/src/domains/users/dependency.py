from fastapi import Depends

from src.core.response import AppError
from src.domains.users.repository import UserRepository, Users
from src.domains.users.serivce import UserService
from src.domains._shared.dependencies import AccessTokenBearer
from src.domains.users.exceptions import UserNotFoundError


async def get_current_user(
    token_data=Depends(AccessTokenBearer()),
):
    user_uid = token_data["sub"]
    result: Users | None = await UserRepository().get_user_by_id(user_id=user_uid)
    if result is not None:
        return result

    raise AppError(UserNotFoundError(data=None))


def get_user_service() -> UserService:
    return UserService()
