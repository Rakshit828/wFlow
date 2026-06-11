from loguru import logger
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.db.postgres.main import AsyncSessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        session = AsyncSessionLocal()
        yield session
        logger.info("Closing the session.")
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
