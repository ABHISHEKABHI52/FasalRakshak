"""Field business logic — a field is only reachable through its owning farm (docs/12 §6)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.farm import Field
from app.repositories.farm_repository import FarmRepository
from app.repositories.field_repository import FieldRepository
from app.schemas.field import FieldCreate, FieldResponse, FieldUpdate, GeoPoint
from app.utils.geo import make_point_wkt, parse_point_wkt


class FieldService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = FieldRepository(session)
        self.farms = FarmRepository(session)

    @staticmethod
    def to_response(field: Field, location_text: str | None, cycle_count: int = 0) -> FieldResponse:
        parsed = parse_point_wkt(location_text)
        response = FieldResponse.model_validate(field)
        response.location = GeoPoint(lat=parsed[0], lng=parsed[1]) if parsed else None
        response.crop_cycle_count = cycle_count
        return response

    async def list_fields(self, farm_id: uuid.UUID, owner_id: uuid.UUID) -> list[FieldResponse]:
        if await self.farms.get_for_owner(farm_id, owner_id) is None:
            raise NotFoundError(details={"resource": "farm"})
        rows = await self.repo.list_for_farm(farm_id)
        return [self.to_response(field, text, count) for field, text, count in rows]

    async def get_field(self, field_id: uuid.UUID, owner_id: uuid.UUID) -> FieldResponse:
        result = await self.repo.get_for_owner(field_id, owner_id)
        if result is None:
            raise NotFoundError(details={"resource": "field"})
        field, location_text, cycle_count = result
        return self.to_response(field, location_text, cycle_count)

    async def create_field(self, owner_id: uuid.UUID, data: FieldCreate) -> FieldResponse:
        if await self.farms.get_for_owner(data.farm_id, owner_id) is None:
            raise NotFoundError(details={"resource": "farm"})
        location_wkt = (
            make_point_wkt(data.location.lat, data.location.lng) if data.location else None
        )
        field = await self.repo.create(data, location_wkt=location_wkt)
        return self.to_response(field, location_wkt, 0)

    async def update_field(
        self, field_id: uuid.UUID, owner_id: uuid.UUID, data: FieldUpdate
    ) -> FieldResponse:
        result = await self.repo.get_for_owner(field_id, owner_id)
        if result is None:
            raise NotFoundError(details={"resource": "field"})
        field, _, cycle_count = result
        location_wkt = (
            make_point_wkt(data.location.lat, data.location.lng)
            if data.location is not None
            else None
        )
        await self.repo.apply_update(field, data, location_wkt=location_wkt)
        return self.to_response(field, location_wkt, cycle_count)

    async def archive_field(self, field_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        result = await self.repo.get_for_owner(field_id, owner_id)
        if result is None:
            raise NotFoundError(details={"resource": "field"})
        await self.repo.archive(result[0])