"""Farm persistence — every read is scoped to the owning user (docs/12 §6)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm import Farm, Field
from app.schemas.farm import FarmCreate, FarmUpdate


class FarmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _field_count_subquery(self):
        return (
            select(func.count(Field.id))
            .where(Field.farm_id == Farm.id, Field.is_active.is_(True))
            .scalar_subquery()
        )

    async def list_for_owner(
        self, owner_id: uuid.UUID, *, include_inactive: bool = False
    ) -> list[tuple[Farm, int]]:
        stmt = select(Farm, self._field_count_subquery().label("field_count")).where(
            Farm.owner_id == owner_id
        )
        if not include_inactive:
            stmt = stmt.where(Farm.is_active.is_(True))
        stmt = stmt.order_by(Farm.created_at.desc())
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], int(row[1] or 0)) for row in rows]

    async def get_for_owner(self, farm_id: uuid.UUID, owner_id: uuid.UUID) -> tuple[Farm, int] | None:
        """Returns None when the farm does not exist OR belongs to someone else (no enumeration)."""
        stmt = select(Farm, self._field_count_subquery().label("field_count")).where(
            Farm.id == farm_id, Farm.owner_id == owner_id
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            return None
        return row[0], int(row[1] or 0)

    async def create(self, owner_id: uuid.UUID, data: FarmCreate) -> Farm:
        farm = Farm(
            owner_id=owner_id,
            name=data.name,
            address=data.address,
            district=data.district,
            state=data.state,
        )
        self.session.add(farm)
        await self.session.flush()
        return farm

    async def apply_update(self, farm: Farm, data: FarmUpdate) -> Farm:
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(farm, field_name, value)
        await self.session.flush()
        return farm

    async def archive(self, farm: Farm) -> None:
        """Soft delete (docs/08 §2 — DELETE archives)."""
        farm.is_active = False
        await self.session.flush()