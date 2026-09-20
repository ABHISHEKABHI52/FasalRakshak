"""Image-quality engine unit tests with synthetic images (docs/00 §16, PROTOTYPE thresholds)."""

from PIL import Image

from app.quality.engine import assess_image
from tests.conftest import make_image_bytes

import io

BANDS = {"min_dimension": 224, "band_good": 80, "band_acceptable": 60, "band_poor": 40}


def _decode(raw: bytes) -> Image.Image:
    return Image.open(io.BytesIO(raw)).convert("RGB")


def test_good_image_scores_good_and_is_usable():
    result = assess_image(_decode(make_image_bytes("good")), **BANDS)
    assert result.category.value == "good"
    assert result.usable is True
    assert result.quality_score >= 80
    assert result.reasons == []


def test_blurry_image_reports_blurry_reason_and_scores_worse():
    result = assess_image(_decode(make_image_bytes("blurry")), **BANDS)
    good = assess_image(_decode(make_image_bytes("good")), **BANDS)
    assert "blurry" in result.reasons  # low sharpness raises a blur flag
    assert result.metrics["sharpness_variance"] < good.metrics["sharpness_variance"]
    assert result.quality_score <= good.quality_score


def test_dark_image_is_unusable():
    result = assess_image(_decode(make_image_bytes("dark")), **BANDS)
    assert result.category.value == "unusable"
    assert result.usable is False
    assert "too_dark" in result.reasons


def test_low_resolution_image_is_unusable():
    result = assess_image(_decode(make_image_bytes("low_res")), **BANDS)
    assert result.category.value == "unusable"
    assert result.usable is False
    assert "low_resolution" in result.reasons
    assert "subject_too_small" in result.reasons


def test_blank_image_reports_missing_subject_and_skips_blur():
    result = assess_image(_decode(make_image_bytes("blank")), **BANDS)
    assert "subject_too_small" in result.reasons
    assert result.leaf_coverage is not None and result.leaf_coverage < 0.05


def test_quality_scores_are_ordered_and_bounded():
    good = assess_image(_decode(make_image_bytes("good")), **BANDS).quality_score
    dark = assess_image(_decode(make_image_bytes("dark")), **BANDS).quality_score
    low_res = assess_image(_decode(make_image_bytes("low_res")), **BANDS).quality_score
    assert 0 <= low_res <= 100 and 0 <= dark <= 100 and 0 <= good <= 100
    assert good > dark and good > low_res