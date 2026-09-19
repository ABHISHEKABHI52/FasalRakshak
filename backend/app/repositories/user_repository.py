"""User persistence (docs/07 §1–2). No business logic here."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role, RoleName, UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.role_links).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.role_links).selectinload(UserRole.role))
            .where(User.phone == phone)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.role_links).selectinload(UserRole.role))
            .where(User.email == email)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_role_id(self, name: RoleName) -> int | None:
        stmt = select(Role.id).where(Role.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        *,
        phone: str,
        password_hash: str,
        full_name: str,
        preferred_language: str,
        district: str | None,
        state: str | None,
        consent_ml_use: bool,
        role_id: int,
    ) -> User:
        user = User(
            phone=phone,
            password_hash=password_hash,
            full_name=full_name,
            preferred_language=preferred_language,
            district=district,
            state=state,
            consent_ml_use=consent_ml_use,
        )
        self.session.add(user)
        await self.session.flush()
        self.session.add(UserRole(user_id=user.id, role_id=role_id))
        await self.session.flush()
        return user
