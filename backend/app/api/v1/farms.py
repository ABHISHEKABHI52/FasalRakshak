"""Farm endpoints (docs/08 §2). Ownership enforced in the service layer (docs/12 §6)."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.farm import FarmCreate, FarmResponse, FarmUpdate
from app.services.farm_service import FarmService

router = APIRouter(prefix="/farms", tags=["farms"])

_farmer = require_role(RoleName.FARMER)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FarmResponse)
async def create_farm(
    data: FarmCreate,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> FarmResponse:
    farm = await FarmService(session).create_farm(user.id, data)
    await session.commit()
    return farm


@router.get("", response_model=list[FarmResponse], summary="List my farms")
async def list_farms(
    user: User = Depends(_farmer), session: AsyncSession = Depends(get_db)
) -> list[FarmResponse]:
    return await FarmService(session).list_farms(user.id)


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: uuid.UUID,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> FarmResponse:
    return await FarmService(session).get_farm(farm_id, user.id)


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: uuid.UUID,
    data: FarmUpdate,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> FarmResponse:
    farm = await FarmService(session).update_farm(farm_id, user.id, data)
    await session.commit()
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Archive farm (soft delete)")
async def archive_farm(
    farm_id: uuid.UUID,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> None:
    await FarmService(session).archive_farm(farm_id, user.id)
    await session.commit()