"""Crop catalogue persistence (controlled vocabulary — docs/00 §27.1)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crop import Crop


class CropRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_crops(self, *, supported_only: bool = False) -> list[Crop]:
        stmt = select(Crop)
        if supported_only:
            stmt = stmt.where(Crop.is_supported.is_(True))
        stmt = stmt.order_by(Crop.code.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_id(self, crop_id: uuid.UUID) -> Crop | None:
        return (
            await self.session.execute(select(Crop).where(Crop.id == crop_id))
        ).scalar_one_or_none()

    async def get_by_code(self, code: str) -> Crop | None:
        return (
            await self.session.execute(select(Crop).where(Crop.code == code))
        ).scalar_one_or_none()