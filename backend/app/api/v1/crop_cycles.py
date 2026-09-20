"""Crop-cycle endpoints (docs/08 §2) — a cycle belongs to a field the farmer owns."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.crop_cycle import CropCycleCreate, CropCycleResponse, CropCycleUpdate
from app.services.crop_cycle_service import CropCycleService

router = APIRouter(prefix="/crop-cycles", tags=["crop-cycles"])

_farmer = require_role(RoleName.FARMER)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CropCycleResponse)
async def create_crop_cycle(
    data: CropCycleCreate,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> CropCycleResponse:
    cycle = await CropCycleService(session).create_cycle(user.id, data)
    await session.commit()
    return cycle


@router.get("", response_model=list[CropCycleResponse], summary="Crop cycles of one of my fields")
async def list_crop_cycles(
    field_id: uuid.UUID = Query(..., description="Field to list crop cycles for"),
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> list[CropCycleResponse]:
    return await CropCycleService(session).list_cycles(field_id, user.id)


@router.get("/{cycle_id}", response_model=CropCycleResponse)
async def get_crop_cycle(
    cycle_id: uuid.UUID,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> CropCycleResponse:
    return await CropCycleService(session).get_cycle(cycle_id, user.id)


@router.patch("/{cycle_id}", response_model=CropCycleResponse)
async def update_crop_cycle(
    cycle_id: uuid.UUID,
    data: CropCycleUpdate,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> CropCycleResponse:
    cycle = await CropCycleService(session).update_cycle(cycle_id, user.id, data)
    await session.commit()
    return cycle