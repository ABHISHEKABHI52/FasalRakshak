"""Field persistence. Ownership is resolved through farm.owner_id in SQL (docs/12 §6)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import is_postgres_dialect
from app.models.crop import CropCycle
from app.models.farm import Farm, Field
from app.schemas.field import FieldCreate, FieldUpdate

if is_postgres_dialect():
    from sqlalchemy import func as _sa_func

    def _location_text_expr():
        # geography -> EWKT text so the API can return {lat, lng}
        return _sa_func.ST_AsText(Field.location).label("location_text")
else:

    def _location_text_expr():
        # SQLite stores the WKT string directly (test-only approximation)
        return Field.location.label("location_text")


class FieldRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _cycle_count_subquery(self):
        return (
            select(func.count(CropCycle.id))
            .where(CropCycle.field_id == Field.id)
            .scalar_subquery()
        )

    async def list_for_farm(
        self, farm_id: uuid.UUID, *, include_inactive: bool = False
    ) -> list[tuple[Field, str | None, int]]:
        stmt = select(
            Field, _location_text_expr(), self._cycle_count_subquery().label("cycle_count")
        ).where(Field.farm_id == farm_id)
        if not include_inactive:
            stmt = stmt.where(Field.is_active.is_(True))
        stmt = stmt.order_by(Field.created_at.asc())
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1], int(row[2] or 0)) for row in rows]

    async def get_for_owner(
        self, field_id: uuid.UUID, owner_id: uuid.UUID
    ) -> tuple[Field, str | None, int] | None:
        stmt = (
            select(Field, _location_text_expr(), self._cycle_count_subquery().label("cycle_count"))
            .join(Farm, Field.farm_id == Farm.id)
            .where(Field.id == field_id, Farm.owner_id == owner_id)
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            return None
        return row[0], row[1], int(row[2] or 0)

    async def get_by_id(self, field_id: uuid.UUID) -> Field | None:
        return (
            await self.session.execute(select(Field).where(Field.id == field_id))
        ).scalar_one_or_none()

    async def create(self, data: FieldCreate, *, location_wkt: str | None) -> Field:
        field = Field(
            farm_id=data.farm_id,
            name=data.name,
            area_hectares=data.area_hectares,
            location=location_wkt,
            soil_type=data.soil_type,
            district_code=data.district_code,
        )
        self.session.add(field)
        await self.session.flush()
        return field

    async def apply_update(
        self, field: Field, data: FieldUpdate, *, location_wkt: str | None
    ) -> Field:
        payload = data.model_dump(exclude_unset=True)
        payload.pop("location", None)
        for field_name, value in payload.items():
            setattr(field, field_name, value)
        if "location" in data.model_fields_set:
            field.location = location_wkt
        await self.session.flush()
        return field

    async def archive(self, field: Field) -> None:
        field.is_active = False
        await self.session.flush()