from fastapi import Request, Depends
from typing import AsyncGenerator, Self
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.db.postgres.schemas import Users
from src.core.response import AppError
from src.domains._shared.exceptions import (
    EmptySessionTokenError,
    InvalidSessionTokenError,
    SessionTokenExpiredError,
)
from src.core.security import hash_session_token
from src.db.postgres.main import AsyncSessionLocal
from src.domains.users.repository import SessionRepository
from loguru import logger
from src.core.response import AppError
from pydantic import BaseModel, ConfigDict
from src.domains._shared.constants import SESSION_COOKIE_NAME


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        session = AsyncSessionLocal()
        yield session
        logger.info("Closing the session.")
    except Exception as e:
        logger.info("Doing rollback.")
        await session.rollback()
        raise e
    finally:
        await session.close()


class UserAndSessionData(BaseModel):
    user: Users
    session: AsyncSession

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_user(self) -> Users:
        if not self.user:
            raise AppError()
        return self.user

    def get_session(self) -> AsyncSession:
        if not self.session:
            raise AppError()
        return self.session


async def get_user_and_session(
    request: Request,
    session_repo: SessionRepository = Depends(SessionRepository),
    session: AsyncSession = Depends(get_session),
):
    logger.info(f"Running DI")

    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        raise AppError(EmptySessionTokenError(data=None))

    token_hash = hash_session_token(token)
    user = await session_repo.get_user_by_token(session, token_hash)

    if not user:
        raise AppError(InvalidSessionTokenError(data=None))

    return UserAndSessionData(user=user, session=session)
