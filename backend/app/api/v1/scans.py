"""Scan endpoints (docs/08 §3): create (idempotent), history, detail, upload, image view.

Ownership is enforced in the service layer; uploads are size-capped and validated by
`app/quality/validation.py` (magic bytes — never the filename extension).
"""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps as api_deps
from app.api.deps import get_scan_service
from app.auth.deps import require_role
from app.core.errors import PayloadTooLargeError
from app.models.role import RoleName
from app.models.user import User
from app.schemas.scan import (
    ImageUploadResponse,
    ScanCreate,
    ScanCreatedResponse,
    ScanListResponse,
    ScanResponse,
)
from app.services.scan_service import ScanService
router = APIRouter(prefix="/scans", tags=["scans"])

_farmer = require_role(RoleName.FARMER)


async def _read_capped(upload: UploadFile, cap: int) -> bytes:
    """Read the upload with a hard size cap — rejects oversized bodies early."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > cap:
            raise PayloadTooLargeError(details={"max_bytes": cap})
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", summary="Create a scan (idempotent via client_scan_uuid)")
async def create_scan(
    data: ScanCreate,
    user: User = Depends(_farmer),
    service: ScanService = Depends(get_scan_service),
) -> JSONResponse:
    """201 on first submission; 200 with the original scan on replay (docs/08 §3)."""
    result, created = await service.create_scan(user.id, data)
    await service.session.commit()
    payload = result.model_dump(mode="json")
    return JSONResponse(status_code=201 if created else 200, content=payload)


@router.get("", response_model=ScanListResponse, summary="My scan history")
async def list_scans(
    field_id: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(_farmer),
    service: ScanService = Depends(get_scan_service),
) -> ScanListResponse:
    result = await service.list_scans(
        user.id, field_id=field_id, cursor=cursor, limit=limit
    )
    await service.session.commit()
    return result


@router.get("/{scan_id}", response_model=ScanResponse, summary="Scan detail (mine only)")
async def get_scan(
    scan_id: uuid.UUID,
    user: User = Depends(_farmer),
    service: ScanService = Depends(get_scan_service),
) -> ScanResponse:
    result = await service.get_scan(scan_id, user.id)
    await service.session.commit()
    return result


@router.post(
    "/{scan_id}/image",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload the scan image (validate -> quality gate -> analysis contract)",
)
async def upload_scan_image(
    scan_id: uuid.UUID,
    image: UploadFile = File(..., description="JPEG, PNG or WebP; max 10 MB"),
    user: User = Depends(_farmer),
    service: ScanService = Depends(get_scan_service),
    max_bytes: int = Depends(api_deps.get_max_upload_bytes),
) -> ImageUploadResponse:
    data = await _read_capped(image, max_bytes)
    await image.close()
    result = await service.upload_image(
        scan_id, user.id, data=data, filename=image.filename
    )
    await service.session.commit()
    return result


@router.get(
    "/{scan_id}/image",
    summary="View my uploaded scan image",
)
async def get_scan_image(
    scan_id: uuid.UUID,
    user: User = Depends(_farmer),
    service: ScanService = Depends(get_scan_service),
) -> FileResponse:
    scan = await service.scans.get_for_owner(scan_id, user.id)
    if scan is None or scan.image is None:
        from app.core.errors import NotFoundError

        raise NotFoundError(details={"resource": "scan_image"})
    path = api_deps.image_store.resolve(scan.image.storage_path)
    await service.session.commit()
    return FileResponse(path, media_type=scan.image.mime_type)