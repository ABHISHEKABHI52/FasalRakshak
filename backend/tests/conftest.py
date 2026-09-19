"""Shared test fixtures (docs/16 §1).

Strategy: per-test SQLite (aiosqlite) database created from Base.metadata.
Phase-1 tables are deliberately portable (docs/07 conventions), so tests run
without PostgreSQL; PostgreSQL + Alembic parity is validated in CI
(.github/workflows/ci.yml) and via `alembic upgrade head` locally.
"""

import itertools
import os
import pathlib
import tempfile

# Configure environment BEFORE importing the app (settings are read at import time).
_TEST_DIR = pathlib.Path(tempfile.mkdtemp(prefix="fr_tests_"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DIR / 'app_default.db'}"
os.environ["JWT_SECRET"] = "test-secret-0123456789abcdefghijklmn"
os.environ["ENV"] = "development"
os.environ["CORS_ORIGINS"] = "http://test"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

import app.models  # noqa: E402,F401  (populates metadata)
from app.api.deps import auth_rate_limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.role import Role, RoleName  # noqa: E402
from app.models.user import User  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402


_db_counter = itertools.count()


@pytest_asyncio.fixture
async def db():
    """Function-scoped session against a fresh per-test SQLite schema (roles seeded)."""
    db_file = _TEST_DIR / f"test_{next(_db_counter)}.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        for idx, role in enumerate(RoleName, start=1):
            session.add(Role(id=idx, name=role, description=None))
        await session.commit()
        yield session
        await session.execute(delete(User))
        await session.commit()
    await engine.dispose()
    db_file.unlink(missing_ok=True)


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    auth_rate_limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


async def create_user_with_role(
    db,
    phone: str,
    role: RoleName,
    password: str = "password123",
) -> User:
    """Test helper: create an active user with a specific role."""
    repo = UserRepository(db)
    role_id = await repo.get_role_id(role)
    assert role_id is not None, f"role {role} missing"
    user = await repo.create(
        phone=phone,
        password_hash=hash_password(password),
        full_name="Test User",
        preferred_language="en",
        district=None,
        state=None,
        consent_ml_use=False,
        role_id=role_id,
    )
    await db.commit()
    return user


async def role_count(db) -> int:
    return len((await db.execute(select(Role))).scalars().all())
