"""Crop catalogue + crop-cycle business logic (docs/08 §2)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, UnprocessableError
from app.models.crop import Crop, CropCycle
from app.repositories.crop_cycle_repository import CropCycleRepository, derive_stage
from app.repositories.crop_repository import CropRepository
from app.repositories.field_repository import FieldRepository
from app.schemas.crop import CropResponse
from app.schemas.crop_cycle import CropCycleCreate, CropCycleResponse, CropCycleUpdate


class CropService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CropRepository(session)

    async def list_crops(self) -> list[CropResponse]:
        crops = await self.repo.list_crops()
        return [CropResponse.model_validate(crop) for crop in crops]

    async def get_supported(self, crop_id: uuid.UUID) -> Crop:
        crop = await self.repo.get_by_id(crop_id)
        if crop is None:
            raise NotFoundError(details={"resource": "crop"})
        return crop


class CropCycleService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CropCycleRepository(session)
        self.fields = FieldRepository(session)
        self.crops = CropRepository(session)

    @staticmethod
    def to_response(cycle: CropCycle, crop: Crop) -> CropCycleResponse:
        return CropCycleResponse(
            id=cycle.id,
            field_id=cycle.field_id,
            crop_id=cycle.crop_id,
            crop_code=crop.code,
            crop_name_en=crop.name_en,
            crop_name_hi=crop.name_hi,
            variety=cycle.variety,
            sowing_date=cycle.sowing_date,
            expected_harvest_date=cycle.expected_harvest_date,
            current_stage=cycle.current_stage,
            stage_updated_at=cycle.stage_updated_at,
            status=cycle.status,
            created_at=cycle.created_at,
            updated_at=cycle.updated_at,
        )

    async def list_cycles(self, field_id: uuid.UUID, owner_id: uuid.UUID) -> list[CropCycleResponse]:
        if await self.fields.get_for_owner(field_id, owner_id) is None:
            raise NotFoundError(details={"resource": "field"})
        rows = await self.repo.list_for_field(field_id)
        return [self.to_response(cycle, crop) for cycle, crop in rows]

    async def get_cycle(self, cycle_id: uuid.UUID, owner_id: uuid.UUID) -> CropCycleResponse:
        result = await self.repo.get_for_owner(cycle_id, owner_id)
        if result is None:
            raise NotFoundError(details={"resource": "crop_cycle"})
        cycle, crop = result
        return self.to_response(await self.repo.refresh_stage(cycle, crop), crop)

    async def create_cycle(self, owner_id: uuid.UUID, data: CropCycleCreate) -> CropCycleResponse:
        if await self.fields.get_for_owner(data.field_id, owner_id) is None:
            raise NotFoundError(details={"resource": "field"})
        crop = await self.crops.get_by_id(data.crop_id)
        if crop is None:
            raise NotFoundError(details={"resource": "crop"})
        if not crop.is_supported:
            raise UnprocessableError(
                code="crop_not_supported",
                message_key="errors.crop_not_supported",
                details={"crop_code": crop.code},
            )
        stage = derive_stage(data.sowing_date, crop.stage_model)
        cycle = await self.repo.create(data, stage=stage)
        return self.to_response(cycle, crop)

    async def update_cycle(
        self, cycle_id: uuid.UUID, owner_id: uuid.UUID, data: CropCycleUpdate
    ) -> CropCycleResponse:
        result = await self.repo.get_for_owner(cycle_id, owner_id)
        if result is None:
            raise NotFoundError(details={"resource": "crop_cycle"})
        cycle, crop = result
        await self.repo.apply_update(cycle, data)
        return self.to_response(cycle, crop)