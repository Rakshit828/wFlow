"""FastAPI dependencies for route protection via JWT cookies."""

import uuid

from fastapi import Request, Depends, HTTPException, status
import jwt

from src.services.tokens import verify_token
from src.db.postgres.setup import get_session, AsyncSession
from src.repositories.auth_repository import UserRepository
from src.db.postgres.schemas import User


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user_repo: UserRepository = Depends(UserRepository),
) -> User:
    """Extract and validate the access_token cookie, then return the User.

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            ...
    """
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = verify_token(token, expected_type="access")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
        )
    except (jwt.InvalidTokenError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid access token: {e}",
        )

    user_id = payload.get("sub")
    user = await user_repo.get_user_by_id(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user
