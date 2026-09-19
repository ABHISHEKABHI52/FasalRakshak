"""Audit logging service (docs/12 §5). Thin wrapper over the append-only repository."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditRepository(session)

    async def record(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        ip_hash: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
    ) -> None:
        await self.repo.record(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_hash=ip_hash,
            before=before,
            after=after,
        )
