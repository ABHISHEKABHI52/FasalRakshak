"""Model registry — importing all models populates Base.metadata for Alembic."""

from app.models.audit_log import AuditLog
from app.models.crop import Crop, CropCycle, CropStage, CycleStatus
from app.models.diagnosis import Diagnosis, DiagnosisStatus
from app.models.farm import Farm, Field
from app.models.refresh_token import RefreshToken
from app.models.role import Role, RoleName, UserRole
from app.models.scan import (
    ALLOWED_IMAGE_MIME_TYPES,
    CropScan,
    ImageAsset,
    ImageQualityResult,
    PlantPart,
    QualityCategory,
    ScanStatus,
)
from app.models.user import User

__all__ = [
    "ALLOWED_IMAGE_MIME_TYPES",
    "AuditLog",
    "Crop",
    "CropCycle",
    "CropScan",
    "CropStage",
    "CycleStatus",
    "Diagnosis",
    "DiagnosisStatus",
    "Farm",
    "Field",
    "ImageAsset",
    "ImageQualityResult",
    "PlantPart",
    "QualityCategory",
    "RefreshToken",
    "Role",
    "RoleName",
    "ScanStatus",
    "User",
    "UserRole",
]
