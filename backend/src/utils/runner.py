from typing import Awaitable, TypeVar
from pymongo.errors import PyMongoError
from loguru import logger
from src.core.response import AppError
from src.core.exceptions import UnexpectedDatabaseError

T = TypeVar("T")


async def safely_run(coroutine: Awaitable[T]) -> T:
    try:
        return await coroutine
    except PyMongoError as e:
        logger.error(f"Error during DB operation occurred. {e}")
        raise AppError(UnexpectedDatabaseError(data=None))
