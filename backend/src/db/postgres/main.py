from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.config import CONFIG

engine = create_async_engine(
    CONFIG.POSTGRES_DB_URL,
    echo=True,  # SQL logging
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass