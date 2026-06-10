from typing import Awaitable, TypeVar
from sqlalchemy import exc
from loguru import logger
from src.core.response import AppError
from src.core.exceptions import UnexpectedDatabaseError

T = TypeVar("T")


async def safely_run(coroutine: Awaitable[T]) -> T:
    try:
        return await coroutine
    except exc.SQLAlchemyError as e:
        logger.error(f"Error during DB operation occurred. {e}")
        raise AppError(UnexpectedDatabaseError(data=None))
