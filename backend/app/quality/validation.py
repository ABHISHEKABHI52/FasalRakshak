"""Image decoding/validation before any storage or analysis (docs/12 §3).

Rules enforced here (never trust the client):
1. size cap, applied to the bytes actually received (not a header claim);
2. format by decoding — magic bytes, not the filename extension;
3. supported formats only: JPEG, PNG, WebP (docs/07 `images` constraint);
4. decode with a pixel-count guard (decompression-bomb protection);
5. truncation/corruption rejected.
"""

import io

from PIL import Image, UnidentifiedImageError

from app.core.errors import BadRequestError, PayloadTooLargeError, UnsupportedMediaError

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
_FORMAT_TO_MIME = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


def decode_upload(data: bytes, *, max_bytes: int, max_pixels: int) -> tuple[Image.Image, str]:
    """Validate + decode raw upload bytes.

    Returns (decoded RGB image, mime type). Raises:
      PayloadTooLargeError (413), UnsupportedMediaError (415), BadRequestError (400).
    """
    if not data:
        raise BadRequestError(code="empty_upload", message_key="errors.empty_upload")
    if len(data) > max_bytes:
        raise PayloadTooLargeError(details={"max_bytes": max_bytes, "received_bytes": len(data)})

    previous_pixel_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = max_pixels  # guards against decompression bombs
    try:
        try:
            with Image.open(io.BytesIO(data)) as probe:
                image_format = probe.format
                probe.verify()  # integrity check; invalidates the handle
        except UnidentifiedImageError as exc:
            raise UnsupportedMediaError(details={"reason": "not_an_image"}) from exc
        except Image.DecompressionBombError as exc:
            raise PayloadTooLargeError(
                details={"reason": "pixel_count_exceeds_limit", "max_pixels": max_pixels}
            ) from exc
        except Exception as exc:  # truncated / corrupt payload
            raise BadRequestError(
                code="invalid_image", message_key="errors.invalid_image"
            ) from exc

        if image_format not in SUPPORTED_FORMATS:
            raise UnsupportedMediaError(
                details={"detected_format": image_format, "supported": sorted(SUPPORTED_FORMATS)}
            )

        # Re-open after verify() and fully load so later processing never sees a lazy handle.
        try:
            with Image.open(io.BytesIO(data)) as reloaded:
                reloaded.load()
                image = reloaded.convert("RGB")
        except Exception as exc:
            raise BadRequestError(code="invalid_image", message_key="errors.invalid_image") from exc
    finally:
        Image.MAX_IMAGE_PIXELS = previous_pixel_limit

    return image, _FORMAT_TO_MIME[str(image_format)]