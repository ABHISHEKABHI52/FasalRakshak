"""Scan persistence, including idempotency lookup and keyset pagination (docs/08 §3)."""

import base64
import binascii
import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError
from app.models.scan import CropScan, PlantPart, ScanStatus

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def encode_cursor(scan: CropScan) -> str:
    raw = f"{scan.created_at.isoformat()}|{scan.id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        timestamp_text, _, scan_id = raw.partition("|")
        return datetime.fromisoformat(timestamp_text), uuid.UUID(scan_id)
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        raise BadRequestError(code="invalid_cursor", message_key="errors.invalid_cursor") from exc


class ScanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        client_scan_uuid: uuid.UUID,
        field_id: uuid.UUID,
        crop_cycle_id: uuid.UUID,
        user_id: uuid.UUID,
        plant_part: PlantPart,
        captured_at: datetime,
    ) -> CropScan:
        scan = CropScan(
            client_scan_uuid=client_scan_uuid,
            field_id=field_id,
            crop_cycle_id=crop_cycle_id,
            user_id=user_id,
            plant_part=plant_part,
            captured_at=captured_at,
            status=ScanStatus.PENDING_IMAGE,
        )
        self.session.add(scan)
        await self.session.flush()
        return scan

    async def get_by_client_uuid(self, client_scan_uuid: uuid.UUID) -> CropScan | None:
        return (
            await self.session.execute(
                select(CropScan).where(CropScan.client_scan_uuid == client_scan_uuid)
            )
        ).scalar_one_or_none()

    async def get_for_owner(self, scan_id: uuid.UUID, owner_id: uuid.UUID) -> CropScan | None:
        """Returns None for both missing and not-owned scans (docs/12 §6 — no enumeration)."""
        return (
            await self.session.execute(
                select(CropScan).where(CropScan.id == scan_id, CropScan.user_id == owner_id)
            )
        ).scalar_one_or_none()

    async def list_for_owner(
        self,
        owner_id: uuid.UUID,
        *,
        field_id: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[CropScan], str | None]:
        limit = max(1, min(limit, MAX_PAGE_SIZE))
        stmt = select(CropScan).where(CropScan.user_id == owner_id)
        if field_id is not None:
            stmt = stmt.where(CropScan.field_id == field_id)
        if cursor:
            cursor_created_at, cursor_id = decode_cursor(cursor)
            stmt = stmt.where(
                or_(
                    CropScan.created_at < cursor_created_at,
                    and_(CropScan.created_at == cursor_created_at, CropScan.id < cursor_id),
                )
            )
        stmt = stmt.order_by(CropScan.created_at.desc(), CropScan.id.desc()).limit(limit + 1)
        rows = list((await self.session.execute(stmt)).scalars().all())
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = encode_cursor(items[-1]) if has_more and items else None
        return items, next_cursor

    async def set_status(
        self, scan: CropScan, status: ScanStatus, *, reason: str | None = None
    ) -> CropScan:
        scan.status = status
        scan.status_reason = reason
        await self.session.flush()
        return scan