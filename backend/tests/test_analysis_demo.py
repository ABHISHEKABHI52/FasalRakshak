"""Phase 3 deterministic demo classifier tests."""

import uuid
from pathlib import Path

from app.analysis.service import (
    AnalysisStatus,
    DeterministicDemoClassifier,
)


def _make_context(
    quality_score: int = 80,
    quality_category: str = "good",
    crop_code: str = "tomato",
    crop_stage: str = "vegetative",
    district: str | None = None,
):
    """Build a minimal AnalysisContext for deterministic testing."""
    return type(
        "AnalysisContext",
        (),
        {
            "scan_id": uuid.uuid4(),
            "image_path": Path("/tmp/test.jpg"),
            "crop_code": crop_code,
            "crop_stage": crop_stage,
            "plant_part": "leaf",
            "field_id": uuid.uuid4(),
            "district": district,
            "quality_score": quality_score,
            "quality_category": quality_category,
        },
    )()


def test_demo_classifier_same_input_same_output():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=90, quality_category="good")
    r1 = svc.analyze(ctx)
    r2 = svc.analyze(ctx)
    assert r1.model_name == "deterministic_demo_classifier"
    assert r1.model_version == "demo-1.0"
    assert r1.is_mock is False
    assert r1.status == AnalysisStatus.DIAGNOSED
    assert r1.confidence == r2.confidence
    assert r1.primary_label_code == r2.primary_label_code


def test_demo_classifier_good_quality_reaches_analysis():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=85, quality_category="good")
    outcome = svc.analyze(ctx)
    assert outcome.status == AnalysisStatus.DIAGNOSED
    assert outcome.confidence is not None
    assert 0 <= outcome.confidence <= 1.0


def test_demo_classifier_low_quality_returns_insufficient_evidence():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=30, quality_category="unusable")
    outcome = svc.analyze(ctx)
    assert outcome.status == AnalysisStatus.INSUFFICIENT_EVIDENCE
    assert outcome.candidates == []
    assert outcome.primary_label_code is None
    assert outcome.confidence is None


def test_demo_classifier_confidence_bounded():
    svc = DeterministicDemoClassifier()
    for score in (39, 40, 50, 60, 70, 80, 90, 100):
        ctx = _make_context(quality_score=score, quality_category="good")
        outcome = svc.analyze(ctx)
        if outcome.status == AnalysisStatus.DIAGNOSED:
            assert 0 <= outcome.confidence <= 1.0


def test_demo_classifier_model_name_and_provenance():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=80, quality_category="good")
    outcome = svc.analyze(ctx)
    assert outcome.model_name == "deterministic_demo_classifier"
    assert outcome.model_version == "demo-1.0"
    assert outcome.is_mock is False


def test_demo_classifier_evidence_present():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=85, crop_code="tomato", district="Gaya")
    outcome = svc.analyze(ctx)
    assert len(outcome.reasons) >= 5
    assert any("quality_score:" in r for r in outcome.reasons)
    assert any("crop_code:" in r for r in outcome.reasons)
    assert any("district:" in r for r in outcome.reasons)


def test_demo_classifier_insufficient_evidence_has_no_candidates():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=10, quality_category="unusable")
    outcome = svc.analyze(ctx)
    assert outcome.status == AnalysisStatus.INSUFFICIENT_EVIDENCE
    assert outcome.candidates == []


def test_demo_classifier_quality_boundary_60():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=60, quality_category="acceptable")
    outcome = svc.analyze(ctx)
    assert outcome.status == AnalysisStatus.DIAGNOSED
    assert outcome.confidence == 0.45


def test_demo_classifier_quality_boundary_80():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=80, quality_category="good")
    outcome = svc.analyze(ctx)
    assert outcome.status == AnalysisStatus.DIAGNOSED
    assert outcome.confidence == 0.65


def test_demo_classifier_quality_boundary_39():
    svc = DeterministicDemoClassifier()
    ctx = _make_context(quality_score=39, quality_category="poor")
    outcome = svc.analyze(ctx)
    assert outcome.status == AnalysisStatus.INSUFFICIENT_EVIDENCE


def test_demo_classifier_different_crops_same_label():
    svc = DeterministicDemoClassifier()
    ctx1 = _make_context(quality_score=85, crop_code="tomato")
    ctx2 = _make_context(quality_score=85, crop_code="rice")
    r1 = svc.analyze(ctx1)
    r2 = svc.analyze(ctx2)
    assert r1.primary_label_code == r2.primary_label_code