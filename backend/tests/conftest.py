"""Shared test fixtures (docs/16 §1).

Strategy: per-test SQLite (aiosqlite) database created from Base.metadata.
Phase-1 tables are deliberately portable (docs/07 conventions), so tests run
without PostgreSQL; PostgreSQL + Alembic parity is validated in CI
(.github/workflows/ci.yml) and via `alembic upgrade head` locally.
"""

import itertools
import io
import os
import pathlib
import tempfile

# Configure environment BEFORE importing the app (settings are read at import time).
_TEST_DIR = pathlib.Path(tempfile.mkdtemp(prefix="fr_tests_"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DIR / 'app_default.db'}"
os.environ["JWT_SECRET"] = "test-secret-0123456789abcdefghijklmn"
os.environ["ENV"] = "development"
os.environ["CORS_ORIGINS"] = "http://test"
os.environ["MEDIA_DIR"] = str(_TEST_DIR / "media")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

import app.models  # noqa: E402,F401  (populates metadata)
from app.analysis.service import (  # noqa: E402
    AnalysisCandidate,
    AnalysisOutcome,
    AnalysisStatus,
    DeterministicDemoClassifier,
    get_analysis_service,
)
from app.api.deps import auth_rate_limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.role import Role, RoleName  # noqa: E402
from app.models.crop import Crop  # noqa: E402
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
        # Crop catalogue seed (mirrors migration 0002 — single source: app/db/seed_data.py).
        from app.db.seed_data import CROP_SEED

        for entry in CROP_SEED:
            session.add(Crop(**entry))
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


# ---------- Phase 2 helpers: images + farmer tree ----------


def make_image_bytes(kind: str = "good") -> bytes:
    """Synthetic deterministic test images for the quality gate."""
    if kind == "low_res":
        image = Image.new("RGB", (100, 80), (70, 150, 70))
    elif kind == "dark":
        image = Image.new("RGB", (800, 600), (8, 14, 8))
    elif kind == "blurry":
        image = _leaf_like_image().filter(ImageFilter.GaussianBlur(radius=2))
    elif kind == "blank":
        image = Image.new("RGB", (800, 600), (128, 128, 128))
    else:
        image = _leaf_like_image()
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def _leaf_like_image() -> Image.Image:
    """A high-contrast 'leaf' so the blur heuristic sees real texture."""
    image = Image.new("RGB", (900, 700), (52, 118, 52))
    draw = ImageDraw.Draw(image)
    draw.ellipse((150, 100, 750, 600), fill=(74, 158, 74), outline=(40, 96, 40), width=6)
    draw.line((450, 130, 450, 570), fill=(30, 80, 30), width=8)
    for offset in range(-200, 201, 40):
        draw.line(
            (450, 350 + abs(offset) // 4, 450 + offset, 350 + offset),
            fill=(34, 92, 34),
            width=4,
        )
    import random

    rng = random.Random(42)
    for _ in range(900):
        x = rng.randint(180, 720)
        y = rng.randint(130, 570)
        shade = rng.randint(-26, 26)
        draw.point((x, y), fill=(74 + shade, 158 + shade, 74 + shade))
    return image


class DeterministicTestAnalysisService:
    """TEST double for the analysis contract — MUST NOT be treated as a real model.

    Deterministic output; every stored row is flagged is_mock=True.
    """

    model_name = "test-double"
    model_version = "0-test"

    def analyze(self, context) -> AnalysisOutcome:  # type: ignore[no-untyped-def]
        return AnalysisOutcome(
            status=AnalysisStatus.DIAGNOSED,
            candidates=[AnalysisCandidate(label_code="test_disease", confidence=0.91)],
            primary_label_code="test_disease",
            confidence=0.91,
            reasons=["test_double"],
            model_name=self.model_name,
            model_version=self.model_version,
            inference_ms=0,
            is_mock=True,
        )


@pytest_asyncio.fixture
async def mock_analysis(client):
    """Overrides the analysis service with the deterministic TEST double."""
    stub = DeterministicTestAnalysisService()
    app.dependency_overrides[get_analysis_service] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_analysis_service, None)


@pytest_asyncio.fixture
async def demo_analysis(client):
    """Overrides the analysis service with the real deterministic demo classifier."""
    stub = DeterministicDemoClassifier()
    app.dependency_overrides[get_analysis_service] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_analysis_service, None)


@pytest_asyncio.fixture
async def farmer(client, db):
    """Register + log in a farmer via the real API; returns auth context."""
    payload = {
        "phone": "+919700000100",
        "password": "farmer-pass-123",
        "full_name": "Phase2 Farmer",
        "preferred_language": "hi",
    }
    register = await client.post("/api/v1/auth/register", json=payload)
    assert register.status_code in (201, 409)
    login = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": payload["phone"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {
        "user_id": login.json()["user"]["id"],
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest_asyncio.fixture
async def farm_tree(client, farmer):
    """farm → field → crop-cycle for the farmer (real API calls)."""
    headers = farmer["headers"]
    farm = (
        await client.post(
            "/api/v1/farms",
            json={"name": "Main Farm", "district": "Gaya", "state": "Bihar"},
            headers=headers,
        )
    ).json()
    field = (
        await client.post(
            "/api/v1/fields",
            json={
                "farm_id": farm["id"],
                "name": "North Plot",
                "area_hectares": 1.5,
                "location": {"lat": 24.79, "lng": 85.0},
            },
            headers=headers,
        )
    ).json()
    crops = (await client.get("/api/v1/crops", headers=headers)).json()
    tomato = next((c for c in crops if c["code"] == "tomato"), None)
    assert tomato is not None, f"tomato missing from catalogue: {crops}"
    cycle = (
        await client.post(
            "/api/v1/crop-cycles",


# ---------- image fixtures for upload tests ----------

import io
from PIL import Image as PILImage  # noqa: PLC0415


def _make_test_image_bytes(kind: str = "good") -> bytes:  # noqa: PLC0415
    """Create synthetic JPEG bytes for upload tests."""
    if kind == "good":
        img = PILImage.new("RGB", (800, 600), color=(100, 140, 100))
    elif kind == "bad":
        img = PILImage.new("RGB", (32, 32), color=(30, 30, 30))
    else:
        img = PILImage.new("RGB", (800, 600), color=(100, 140, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def good_test_image():
    """BytesIO of a good-quality green test image."""
    return io.BytesIO(_make_test_image_bytes("good"))


@pytest.fixture
def bad_test_image():
    """BytesIO of a small dark unusable test image."""
    return io.BytesIO(_make_test_image_bytes("bad"))

            json={
                "field_id": field["id"],
                "crop_id": tomato["id"],
                "variety": "Pusa Ruby",
                "sowing_date": "2026-01-10",
            },
            headers=headers,
        )
    ).json()
    assert farm["id"] and field["id"] and cycle["id"]
    return {"farm": farm, "field": field, "cycle": cycle, "crops": crops, "tomato": tomato}
