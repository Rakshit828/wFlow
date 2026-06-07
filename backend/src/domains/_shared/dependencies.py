from fastapi import Request, Depends
from fastapi.security import APIKeyCookie
import jwt

from src.core.security import decode_jwt_tokens
from src.core.response import AppError
from src.domains.users.repository import UserRepository, Users
from .exceptions import JwtTokenExpiredError, InvalidJwtTokenError


class RefreshTokenBearer(APIKeyCookie):
    def __init__(self):
        super().__init__(name="refresh_token", auto_error=False)

    async def __call__(self, request: Request):
        refresh_token = await super().__call__(request=request)
        if refresh_token is None:
            raise AppError(InvalidJwtTokenError(data=None))
        try:
            decoded_token = decode_jwt_tokens(jwt_token=refresh_token)
        except jwt.ExpiredSignatureError:
            raise AppError(JwtTokenExpiredError(data=None))
        except jwt.InvalidJwtTokenError:
            raise AppError(InvalidJwtTokenError(data=None))

        return decoded_token


class AccessTokenBearer(APIKeyCookie):
    def __init__(self):
        super().__init__(name="access_token", auto_error=False)

    async def __call__(self, request: Request):
        access_token = await super().__call__(request=request)
        if access_token is None:
            raise AppError(InvalidJwtTokenError(data=None))
        try:
            decoded_token = decode_jwt_tokens(jwt_token=access_token)
        except jwt.ExpiredSignatureError:
            raise AppError(JwtTokenExpiredError(data=None))
        except jwt.InvalidJwtTokenError:
            raise AppError(InvalidJwtTokenError(data=None))
        return decoded_token


async def get_current_user(
    token_data=Depends(AccessTokenBearer()),
):
    user_uid = token_data["sub"]
    result: Users | None = await UserRepository().get_user_by_id(user_id=user_uid)
    if result is not None:
        return result

    raise AppError()


# class RoleChecker:
#     def __init__(self, allowed_roles: list[str]):
#         self.allowed_roles = allowed_roles

#     def __call__(self, user: Users = Depends(get_current_user)):
#         if user.role not in self.allowed_roles:
#             raise AppError(data=None, detail=AuthErrors.PERMISSION_DENIED_ERROR.value)


# admin_checker = RoleChecker(["admin"])
