"""Farm business logic — ownership enforced server-side (docs/12 §6)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.farm import Farm
from app.repositories.farm_repository import FarmRepository
from app.schemas.farm import FarmCreate, FarmResponse, FarmUpdate


class FarmService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = FarmRepository(session)

    @staticmethod
    def to_response(farm: Farm, field_count: int = 0) -> FarmResponse:
        response = FarmResponse.model_validate(farm)
        response.field_count = field_count
        return response

    async def list_farms(self, owner_id: uuid.UUID) -> list[FarmResponse]:
        rows = await self.repo.list_for_owner(owner_id)
        return [self.to_response(farm, count) for farm, count in rows]

    async def get_farm(self, farm_id: uuid.UUID, owner_id: uuid.UUID) -> FarmResponse:
        result = await self.repo.get_for_owner(farm_id, owner_id)
        if result is None:
            # Same response whether the farm is missing or owned by someone else.
            raise NotFoundError(details={"resource": "farm"})
        farm, field_count = result
        return self.to_response(farm, field_count)

    async def create_farm(self, owner_id: uuid.UUID, data: FarmCreate) -> FarmResponse:
        farm = await self.repo.create(owner_id, data)
        return self.to_response(farm, 0)

    async def update_farm(
        self, farm_id: uuid.UUID, owner_id: uuid.UUID, data: FarmUpdate
    ) -> FarmResponse:
        result = await self.repo.get_for_owner(farm_id, owner_id)
        if result is None:
            raise NotFoundError(details={"resource": "farm"})
        farm, field_count = result
        await self.repo.apply_update(farm, data)
        return self.to_response(farm, field_count)

    async def archive_farm(self, farm_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        result = await self.repo.get_for_owner(farm_id, owner_id)
        if result is None:
            raise NotFoundError(details={"resource": "farm"})
        await self.repo.archive(result[0])