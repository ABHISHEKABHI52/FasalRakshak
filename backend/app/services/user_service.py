"""Registration + authentication business logic (docs/08 §1, docs/12 §1)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.role import RoleName
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        """Create a FARMER user. Caller commits. Duplicate phone -> 409 (docs/08)."""
        if await self.repo.get_by_phone(data.phone) is not None:
            raise ConflictError(code="duplicate_phone", message_key="errors.duplicate_phone")
        role_id = await self.repo.get_role_id(RoleName.FARMER)
        if role_id is None:
            raise RuntimeError("FARMER role missing — run database migrations")
        return await self.repo.create(
            phone=data.phone,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            preferred_language=data.preferred_language,
            district=data.district,
            state=data.state,
            consent_ml_use=data.consent_ml_use,
            role_id=role_id,
        )

    async def authenticate(self, phone_or_email: str, password: str) -> User:
        """Verify credentials. Raises 401 with a generic message on any failure."""
        user = await self._find_by_phone_or_email(phone_or_email)
        # Verify even when user is None to keep timing roughly uniform.
        reference_hash = user.password_hash if user else _DUMMY_HASH
        ok = verify_password(password, reference_hash)
        if user is None or not ok or not user.is_active:
            raise UnauthorizedError(code="invalid_credentials", message_key="errors.invalid_credentials")
        return user

    async def _find_by_phone_or_email(self, phone_or_email: str) -> User | None:
        if "@" in phone_or_email:
            return await self.repo.get_by_email(phone_or_email.lower())
        return await self.repo.get_by_phone(phone_or_email)


# Argon2 hash of an unrecoverable random value — used to equalize timing when the
# account does not exist. Never a real credential.
_DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHRkYXRh$GFaIlRNbGi3Y0tB3F0RS0kXRZPBnKAWtLpMZZm309A"
