"""Database session and configuration for backend."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from backend.src.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Create async engine
# Use asyncpg driver for PostgreSQL async support
database_url = settings.database_url
if not database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.log_level == "DEBUG",
    future=True,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_async_session_context():
    """Context manager for getting async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_async_session_sync():
    """Synchronous wrapper for getting async session (for Celery tasks)."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_async_session_context())


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
