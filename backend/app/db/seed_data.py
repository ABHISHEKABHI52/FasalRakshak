"""Shared seed data (docs/00 §27.1 — documented MVP catalogue, no invented crops).

Used by Alembic migration 0002 AND by the test fixtures (create_all-based DBs).
Stage thresholds are PROTOTYPE values (docs/07 §2) — not agronomically validated.
"""

CROP_STAGE_PROTOTYPE_MODEL = {
    "seedling_max_days": 14,
    "vegetative_max_days": 35,
    "flowering_max_days": 55,
    "fruiting_max_days": 80,
}

CROP_SEED: list[dict] = [
    {
        "code": "tomato",
        "name_en": "Tomato",
        "name_hi": "टमाटर",
        "scientific_name": "Solanum lycopersicum",
        "stage_model": {**CROP_STAGE_PROTOTYPE_MODEL},
        "is_supported": True,
    },
    {
        "code": "potato",
        "name_en": "Potato",
        "name_hi": "आलू",
        "scientific_name": "Solanum tuberosum",
        "stage_model": {
            "seedling_max_days": 12,
            "vegetative_max_days": 40,
            "flowering_max_days": 55,
            "fruiting_max_days": 70,
        },
        "is_supported": True,
    },
    {
        "code": "cotton",
        "name_en": "Cotton",
        "name_hi": "कपास",
        "scientific_name": "Gossypium hirsutum",
        "stage_model": {
            "seedling_max_days": 18,
            "vegetative_max_days": 55,
            "flowering_max_days": 80,
            "fruiting_max_days": 120,
        },
        "is_supported": True,
    },
]