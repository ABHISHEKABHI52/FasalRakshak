"""Field endpoints (docs/08 §2) — a field is reachable only through its owning farm."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.field import FieldCreate, FieldResponse, FieldUpdate
from app.services.field_service import FieldService

router = APIRouter(prefix="/fields", tags=["fields"])

_farmer = require_role(RoleName.FARMER)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FieldResponse)
async def create_field(
    data: FieldCreate,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> FieldResponse:
    field = await FieldService(session).create_field(user.id, data)
    await session.commit()
    return field


@router.get("", response_model=list[FieldResponse], summary="List fields of one of my farms")
async def list_fields(
    farm_id: uuid.UUID = Query(..., description="Farm to list fields for"),
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> list[FieldResponse]:
    return await FieldService(session).list_fields(farm_id, user.id)


@router.get("/{field_id}", response_model=FieldResponse)
async def get_field(
    field_id: uuid.UUID,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> FieldResponse:
    return await FieldService(session).get_field(field_id, user.id)


@router.patch("/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: uuid.UUID,
    data: FieldUpdate,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> FieldResponse:
    field = await FieldService(session).update_field(field_id, user.id, data)
    await session.commit()
    return field


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Archive field (soft delete)")
async def archive_field(
    field_id: uuid.UUID,
    user: User = Depends(_farmer),
    session: AsyncSession = Depends(get_db),
) -> None:
    await FieldService(session).archive_field(field_id, user.id)
    await session.commit()