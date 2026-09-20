"""API v1 router aggregation (docs/08)."""

from fastapi import APIRouter

from app.api.v1 import admin, auth, crop_cycles, crops, farms, fields, health, scans

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(farms.router)
api_router.include_router(fields.router)
api_router.include_router(crops.router)
api_router.include_router(crop_cycles.router)
api_router.include_router(scans.router)
