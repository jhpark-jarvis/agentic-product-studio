from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/health")
async def health(request: Request):
    settings = request.app.state.settings
    return {
        "ok": True,
        "service": "personal-service-fastapi",
        "repository_backend": settings.repository_backend,
        "storage_backend": settings.storage_backend,
        "database_path": settings.database if settings.repository_backend == "sqlite" else "",
    }


@router.get("/api/runtime-summary")
async def runtime_summary(request: Request):
    settings = request.app.state.settings
    return {
        "runtime": "fastapi",
        "repository_backend": settings.repository_backend,
        "storage_backend": settings.storage_backend,
        "cloudflare_configured": bool(settings.cloudflare_account_id and settings.d1_database_id),
        "r2_public_base_url_configured": bool(settings.r2_public_base_url),
    }


@router.get("/api/migration-status")
async def migration_status():
    return {
        "phase": "core-api-migration",
        "message": "FastAPI handles the core API surface, SPA entry routes, and telemetry endpoints.",
        "next_targets": [
            "deployment entrypoint cleanup",
            "test strategy migration",
            "operational rollout documentation",
            "flask dependency reduction",
        ],
    }
