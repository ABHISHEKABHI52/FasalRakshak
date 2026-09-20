"""Local media store for uploaded images (docs/15 §1 — object storage is FUTURE).

Safety properties (docs/12 §3):
- storage keys are generated server-side (never derived from user input);
- written images are re-encoded (EXIF and any embedded payloads are dropped);
- `resolve()` refuses keys escaping the media root (path-traversal guard).
"""

import uuid
from pathlib import Path

from PIL import Image

from app.core.errors import BadRequestError

_SUBDIR = "scans"


class LocalImageStore:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        (self.base_dir / _SUBDIR).mkdir(parents=True, exist_ok=True)

    def save_scan_image(
        self,
        image: Image.Image,
        *,
        scan_id: uuid.UUID,
        max_dimension: int,
        jpeg_quality: int,
    ) -> tuple[str, int, int, int]:
        """Re-encode, downscale, and store. Returns (relative_key, bytes, width, height)."""
        prepared = image.copy()
        if max(prepared.size) > max_dimension:
            prepared.thumbnail((max_dimension, max_dimension))

        key = f"{_SUBDIR}/{scan_id}/{uuid.uuid4().hex}.jpg"
        target = self.base_dir / key
        target.parent.mkdir(parents=True, exist_ok=True)
        prepared.save(target, format="JPEG", quality=jpeg_quality, optimize=True)
        return key, target.stat().st_size, prepared.width, prepared.height

    def resolve(self, key: str) -> Path:
        """Resolve a stored key, refusing anything outside the media root."""
        candidate = (self.base_dir / key).resolve()
        if self.base_dir not in candidate.parents and candidate != self.base_dir:
            raise BadRequestError(code="invalid_media_key", message_key="errors.invalid_media_key")
        if not candidate.is_file():
            raise BadRequestError(code="media_missing", message_key="errors.media_missing")
        return candidate