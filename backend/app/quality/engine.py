"""Image-quality gate — the first real processing stage of the pipeline (docs/00 §16).

Implementations are **heuristics, not a trained model**: no CNN head exists yet
(that is Phase 3+). The scoring weights and thresholds below are the PROTOTYPE
constants described in docs/00 §16 and are NOT scientifically validated; they are
configurable and expected to be tuned against real field captures (docs/18).

Dimensions evaluated: resolution · blur (Laplacian-variance proxy) · brightness ·
darkness · glare · leaf coverage (excess-green heuristic).
Output: quality_score 0-100, category GOOD/ACCEPTABLE/POOR/UNUSABLE, reasons, usable.
"""

from dataclasses import dataclass, field

from PIL import Image, ImageFilter, ImageStat

from app.models.scan import QualityCategory

# ---- PROTOTYPE constants (docs/00 §16 — tunable, not validated) ----
BLUR_REFERENCE_VARIANCE = 150.0
BRIGHTNESS_DARK_MEAN = 60.0
BRIGHTNESS_BRIGHT_MEAN = 190.0
DARK_PIXEL_THRESHOLD = 25
GLARE_PIXEL_THRESHOLD = 248
DARK_FRACTION_LIMIT = 0.50
GLARE_FRACTION_LIMIT = 0.15
LEAF_COVERAGE_TARGET = 0.25
EXCESS_GREEN_MARGIN = 12
SAMPLE_MAX_SIDE = 512
WEIGHTS = {"blur": 0.30, "exposure": 0.25, "resolution": 0.15, "leaf": 0.30}

_LAPLACIAN_KERNEL = ImageFilter.Kernel((3, 3), (0, 1, 0, 1, -4, 1, 0, 1, 0), scale=1, offset=0)

_REASON_HINTS = {
    "blurry": "Hold the phone steady and let the camera focus on the leaf.",
    "too_dark": "Move to better light (open shade or daylight).",
    "too_bright": "Avoid direct harsh sunlight or flash on the leaf.",
    "glare": "Change the angle so bright reflections are not covering the leaf.",
    "subject_too_small": "Move closer so the leaf fills most of the frame.",
    "low_resolution": "Use a higher camera resolution or move closer.",
}


@dataclass(frozen=True)
class QualityAssessment:
    quality_score: int
    category: QualityCategory
    reasons: list[str] = field(default_factory=list)
    usable: bool = True
    leaf_coverage: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)

    def reasons_payload(self) -> dict:
        """JSONB payload for image_quality_results.reasons (code + i18n key + hint)."""
        return {
            "codes": self.reasons,
            "items": [
                {"code": code, "message_key": f"quality.{code}", "hint": _REASON_HINTS.get(code, "")}
                for code in self.reasons
            ],
            "metrics": self.metrics,
            "thresholds_note": "prototype thresholds — not agronomically validated (docs/00 §16)",
        }


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _brightness_subscore(mean: float) -> float:
    if mean < BRIGHTNESS_DARK_MEAN:
        return _clamp(mean / BRIGHTNESS_DARK_MEAN * 100)
    if mean > BRIGHTNESS_BRIGHT_MEAN:
        return _clamp((255 - mean) / (255 - BRIGHTNESS_BRIGHT_MEAN) * 100)
    return 100.0


def _leaf_coverage_ratio(sample: Image.Image) -> float:
    """Excess-green heuristic: fraction of pixels where green clearly dominates."""
    total = sample.width * sample.height
    if total == 0:
        return 0.0
    raw = sample.convert("RGB").tobytes()  # avoids deprecated Image.getdata()
    leafy = 0
    for index in range(0, len(raw), 3):
        r = raw[index]
        g = raw[index + 1]
        b = raw[index + 2]
        if g > r + EXCESS_GREEN_MARGIN and g > b + EXCESS_GREEN_MARGIN:
            leafy += 1
    return leafy / total


def assess_image(
    image: Image.Image,
    *,
    min_dimension: int,
    band_good: int,
    band_acceptable: int,
    band_poor: int,
) -> QualityAssessment:
    """Score an already-decoded, orientation-normalised RGB image."""
    full_width, full_height = image.size

    # Bounded work: analyse a downscaled sample, never the full-resolution bitmap.
    sample = image.copy()
    sample.thumbnail((SAMPLE_MAX_SIDE, SAMPLE_MAX_SIDE))
    gray = sample.convert("L")

    # Blur — variance of a Laplacian-filtered image.
    variance = ImageStat.Stat(gray.filter(_LAPLACIAN_KERNEL)).var[0]
    # Exposure — luminance histogram statistics.
    histogram = gray.histogram()
    pixels = sum(histogram) or 1
    mean_luminance = sum(i * count for i, count in enumerate(histogram)) / pixels
    dark_fraction = sum(histogram[:DARK_PIXEL_THRESHOLD]) / pixels
    glare_fraction = sum(histogram[GLARE_PIXEL_THRESHOLD + 1 :]) / pixels
    # Leaf visibility — excess-green heuristic on the sample.
    leaf_coverage = _leaf_coverage_ratio(sample)

    blur_sub = _clamp(variance / BLUR_REFERENCE_VARIANCE * 100)
    exposure_sub = _clamp(
        0.5 * _brightness_subscore(mean_luminance)
        + 0.25 * _clamp(100 - dark_fraction / DARK_FRACTION_LIMIT * 100)
        + 0.25 * _clamp(100 - glare_fraction / GLARE_FRACTION_LIMIT * 100)
    )
    resolution_sub = _clamp(min(full_width, full_height) / min_dimension * 100)
    leaf_sub = _clamp(leaf_coverage / LEAF_COVERAGE_TARGET * 100)

    score = int(
        round(
            WEIGHTS["blur"] * blur_sub
            + WEIGHTS["exposure"] * exposure_sub
            + WEIGHTS["resolution"] * resolution_sub
            + WEIGHTS["leaf"] * leaf_sub
        )
    )

    reasons: list[str] = []
    if blur_sub < 55:
        reasons.append("blurry")
    if mean_luminance < BRIGHTNESS_DARK_MEAN or dark_fraction > DARK_FRACTION_LIMIT * 0.6:
        reasons.append("too_dark")
    if mean_luminance > BRIGHTNESS_BRIGHT_MEAN:
        reasons.append("too_bright")
    if glare_fraction > GLARE_FRACTION_LIMIT * 0.5:
        reasons.append("glare")
    if resolution_sub < 60:
        reasons.append("low_resolution")
    if leaf_sub < 50:
        reasons.append("subject_too_small")

    if score >= band_good:
        category = QualityCategory.GOOD
    elif score >= band_acceptable:
        category = QualityCategory.ACCEPTABLE
    elif score >= band_poor:
        category = QualityCategory.POOR
    else:
        category = QualityCategory.UNUSABLE

    # Hard floor: below the minimum usable side the image cannot be analysed at all
    # (docs/00 §16 "resolution check — minimum effective size"). PROTOTYPE rule.
    if min(full_width, full_height) < min_dimension and category is not QualityCategory.UNUSABLE:
        category = QualityCategory.UNUSABLE
        score = min(score, 35)
    if min(full_width, full_height) < min_dimension:
        for reason in ("low_resolution", "subject_too_small"):
            if reason not in reasons:
                reasons.append(reason)

    return QualityAssessment(
        quality_score=score,
        category=category,
        reasons=reasons,
        usable=category is not QualityCategory.UNUSABLE,
        leaf_coverage=round(leaf_coverage, 4),
        metrics={
            "sharpness_variance": round(float(variance), 2),
            "mean_luminance": round(mean_luminance, 2),
            "dark_pixel_fraction": round(dark_fraction, 4),
            "glare_pixel_fraction": round(glare_fraction, 4),
            "leaf_coverage_fraction": round(leaf_coverage, 4),
            "width": full_width,
            "height": full_height,
            "blur_subscore": round(blur_sub, 2),
            "exposure_subscore": round(exposure_sub, 2),
            "resolution_subscore": round(resolution_sub, 2),
            "leaf_subscore": round(leaf_sub, 2),
        },
    )