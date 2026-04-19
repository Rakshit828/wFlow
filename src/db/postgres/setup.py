from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from src.config import CONFIG


async_engine = create_async_engine(
    url=CONFIG.DATABASE_URL,
    echo=True
)

AsyncLocalSession = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncLocalSession() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            session.rollback()
            raise 
