"""Crop-cycle persistence. Ownership resolved through field -> farm in SQL (docs/12 §6)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crop import Crop, CropCycle, CropStage
from app.models.farm import Farm, Field
from app.schemas.crop_cycle import CropCycleCreate, CropCycleUpdate

# Prototype stage thresholds in days since sowing (docs/07 §2 — NOT validated).
DEFAULT_STAGE_MODEL: dict[str, int] = {
    "seedling_max_days": 14,
    "vegetative_max_days": 35,
    "flowering_max_days": 55,
    "fruiting_max_days": 80,
}


def derive_stage(sowing_date, stage_model: dict | None, *, today=None) -> CropStage:
    """Derive the growth stage (prototype day-count model, docs/07 §2)."""
    reference = today or datetime.now(timezone.utc).date()
    days = max(0, (reference - sowing_date).days)
    model = {**DEFAULT_STAGE_MODEL, **(stage_model or {})}
    if days <= int(model["seedling_max_days"]):
        return CropStage.SEEDLING
    if days <= int(model["vegetative_max_days"]):
        return CropStage.VEGETATIVE
    if days <= int(model["flowering_max_days"]):
        return CropStage.FLOWERING
    if days <= int(model["fruiting_max_days"]):
        return CropStage.FRUITING
    return CropStage.MATURITY


class CropCycleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_field(self, field_id: uuid.UUID) -> list[tuple[CropCycle, Crop]]:
        stmt = (
            select(CropCycle, Crop)
            .join(Crop, CropCycle.crop_id == Crop.id)
            .where(CropCycle.field_id == field_id)
            .order_by(CropCycle.sowing_date.desc())
        )
        return [(row[0], row[1]) for row in (await self.session.execute(stmt)).all()]

    async def get_for_owner(
        self, cycle_id: uuid.UUID, owner_id: uuid.UUID
    ) -> tuple[CropCycle, Crop] | None:
        stmt = (
            select(CropCycle, Crop)
            .join(Crop, CropCycle.crop_id == Crop.id)
            .join(Field, CropCycle.field_id == Field.id)
            .join(Farm, Field.farm_id == Farm.id)
            .where(CropCycle.id == cycle_id, Farm.owner_id == owner_id)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row is not None else None

    async def get_by_id(self, cycle_id: uuid.UUID) -> CropCycle | None:
        return (
            await self.session.execute(select(CropCycle).where(CropCycle.id == cycle_id))
        ).scalar_one_or_none()

    async def create(self, data: CropCycleCreate, *, stage: CropStage) -> CropCycle:
        cycle = CropCycle(
            field_id=data.field_id,
            crop_id=data.crop_id,
            variety=data.variety,
            sowing_date=data.sowing_date,
            expected_harvest_date=data.expected_harvest_date,
            current_stage=stage,
            stage_updated_at=datetime.now(timezone.utc),
        )
        self.session.add(cycle)
        await self.session.flush()
        return cycle

    async def apply_update(self, cycle: CropCycle, data: CropCycleUpdate) -> CropCycle:
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(cycle, field_name, value)
        await self.session.flush()
        return cycle

    async def refresh_stage(self, cycle: CropCycle, crop: Crop) -> CropCycle:
        stage = derive_stage(cycle.sowing_date, crop.stage_model)
        if stage is not cycle.current_stage:
            cycle.current_stage = stage
            cycle.stage_updated_at = datetime.now(timezone.utc)
            await self.session.flush()
        return cycle