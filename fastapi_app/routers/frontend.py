from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from ..dependencies import get_settings


router = APIRouter(tags=["frontend"])


def _frontend_dir(project_root: str) -> Path:
    return Path(project_root) / "app" / "static" / "frontend"


def _frontend_index(project_root: str) -> Path:
    return _frontend_dir(project_root) / "index.html"


def _frontend_index_response(project_root: str) -> FileResponse:
    index_path = _frontend_index(project_root)
    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="React frontend build not found. Run the frontend build first.",
        )

    response = FileResponse(index_path)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def _normalize_legacy_path(path: str) -> str:
    normalized = path or ""
    full_path = f"/app/{normalized}".rstrip("/")
    if not full_path:
        return "/"
    return (
        full_path.replace("/app/documents", "/documents", 1)
        .replace("/app/wbs", "/wbs", 1)
        .replace("/app/schedules", "/schedules", 1)
        .replace("/app/members", "/members", 1)
        .replace("/app/dashboard", "/", 1)
        .replace("/app", "/", 1)
    )


def _normalize_short_path(segment: str, path: str | None = None) -> str:
    suffix = f"/{path}" if path else ""
    return {
        "document": f"/documents{suffix}",
        "asset": f"/assets{suffix}",
        "task": f"/wbs{suffix}",
        "schedule": f"/schedules{suffix}",
        "member": f"/members{suffix}",
    }[segment]


@router.get("/", include_in_schema=False)
@router.get("/dashboard", include_in_schema=False)
@router.get("/documents", include_in_schema=False)
@router.get("/documents/{path:path}", include_in_schema=False)
@router.get("/assets", include_in_schema=False)
@router.get("/assets/{path:path}", include_in_schema=False)
@router.get("/wbs", include_in_schema=False)
@router.get("/wbs/{path:path}", include_in_schema=False)
@router.get("/schedules", include_in_schema=False)
@router.get("/schedules/{path:path}", include_in_schema=False)
@router.get("/members", include_in_schema=False)
@router.get("/members/{path:path}", include_in_schema=False)
@router.get("/log", include_in_schema=False)
async def app_index(settings=Depends(get_settings)):
    return _frontend_index_response(settings.project_root)


@router.get("/app", include_in_schema=False)
@router.get("/app/", include_in_schema=False)
async def legacy_app_index():
    return RedirectResponse(url="/", status_code=302)


@router.get("/app/{path:path}", include_in_schema=False)
async def app_routes(path: str):
    return RedirectResponse(url=_normalize_legacy_path(path), status_code=302)


@router.get("/document", include_in_schema=False)
@router.get("/document/", include_in_schema=False)
@router.get("/document/{path:path}", include_in_schema=False)
async def legacy_document_routes(path: str | None = None):
    return RedirectResponse(url=_normalize_short_path("document", path), status_code=302)


@router.get("/asset", include_in_schema=False)
@router.get("/asset/", include_in_schema=False)
@router.get("/asset/{path:path}", include_in_schema=False)
async def legacy_asset_routes(path: str | None = None):
    return RedirectResponse(url=_normalize_short_path("asset", path), status_code=302)


@router.get("/task", include_in_schema=False)
@router.get("/task/", include_in_schema=False)
@router.get("/task/{path:path}", include_in_schema=False)
async def legacy_task_routes(path: str | None = None):
    return RedirectResponse(url=_normalize_short_path("task", path), status_code=302)


@router.get("/schedule", include_in_schema=False)
@router.get("/schedule/", include_in_schema=False)
@router.get("/schedule/{path:path}", include_in_schema=False)
async def legacy_schedule_routes(path: str | None = None):
    return RedirectResponse(url=_normalize_short_path("schedule", path), status_code=302)


@router.get("/member", include_in_schema=False)
@router.get("/member/", include_in_schema=False)
@router.get("/member/{path:path}", include_in_schema=False)
async def legacy_member_routes(path: str | None = None):
    return RedirectResponse(url=_normalize_short_path("member", path), status_code=302)


@router.get("/logs", include_in_schema=False)
@router.get("/logs/", include_in_schema=False)
async def legacy_logs_route():
    return RedirectResponse(url="/log", status_code=302)
