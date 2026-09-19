"""Audit-log persistence (docs/07 §7). Append-only — no update/delete methods by design."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
        self.session.add(
            AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                ip_hash=ip_hash,
                before=before,
                after=after,
            )
        )
        await self.session.flush()
