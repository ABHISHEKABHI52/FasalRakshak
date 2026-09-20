"""Crop catalogue endpoint (docs/08 §2) — read-only controlled vocabulary for farmers."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.crop import CropResponse
from app.services.crop_cycle_service import CropService

router = APIRouter(prefix="/crops", tags=["crops"])


@router.get("", response_model=list[CropResponse], summary="Crop catalogue (controlled vocabulary)")
async def list_crops(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> list[CropResponse]:
    return await CropService(session).list_crops()