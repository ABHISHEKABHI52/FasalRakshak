"""Async engine + session factory (docs/05 §2).

Driver is chosen by DATABASE_URL scheme:
- postgresql+asyncpg://… in deployment (docs/15)
- sqlite+aiosqlite://… only as a local smoke-test fallback (clearly flagged)
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session; commits belong to services."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    """SELECT 1 probe used by /api/v1/ready (docs/08 §10)."""
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# Re-exported so routers can raise a uniform dependency-failure error.
database_unavailable_error = ServiceUnavailableError(
    details={"component": "database"},
    code="db_unavailable",
    message_key="errors.db_unavailable",
)
