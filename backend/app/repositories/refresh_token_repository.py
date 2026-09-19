"""Refresh-token persistence (docs/07 §1)."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_active_by_hash(self, token_hash: str, now: datetime) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(token)
        await self.session.flush()
        return token

    async def revoke(self, token: RefreshToken, now: datetime) -> None:
        token.revoked_at = now
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID, now: datetime) -> int:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
        tokens = (await self.session.execute(stmt)).scalars().all()
        for token in tokens:
            token.revoked_at = now
        await self.session.flush()
        return len(tokens)
