from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.page_view_logging import (
    read_page_view_logs_for_path,
    setup_page_view_logger_for_path,
    write_page_view_log_with_logger,
)
from app.utils import parse_int

from ..dependencies import get_settings


router = APIRouter(prefix="/api", tags=["telemetry"])


def _client_ip(request: Request) -> str:
    forwarded_for = (request.headers.get("X-Forwarded-For") or "").strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "") or ""


@router.post("/telemetry/page-view")
async def track_page_view(
    request: Request,
    payload: dict,
    settings=Depends(get_settings),
):
    path = str(payload.get("path") or "").strip()
    referrer = str(payload.get("referrer") or "").strip()
    visitor_id = str(payload.get("visitor_id") or "").strip()
    session_id = str(payload.get("session_id") or "").strip()
    identity_type = str(payload.get("identity_type") or "anonymous_browser").strip()

    if not path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not visitor_id:
        raise HTTPException(status_code=400, detail="Missing visitor_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")

    logger = setup_page_view_logger_for_path(settings.instance_path)
    write_page_view_log_with_logger(
        logger,
        {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "path": path,
            "referrer": referrer,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "identity_type": identity_type,
            "ip": _client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
        },
    )
    return {"logged": True}


@router.get("/logs/page-views")
async def page_view_logs(
    limit: int = Query(default=200),
    q: str = "",
    visitor_id: str = "",
    settings=Depends(get_settings),
):
    normalized_limit = min(parse_int(limit, default=200, minimum=1), 1000)
    rows = read_page_view_logs_for_path(
        settings.instance_path,
        limit=normalized_limit,
        search=q.strip(),
        visitor_id=visitor_id.strip(),
    )

    unique_visitors = len({row.get("visitor_id") for row in rows if row.get("visitor_id")})
    unique_sessions = len({row.get("session_id") for row in rows if row.get("session_id")})
    unique_paths = len({row.get("path") for row in rows if row.get("path")})

    return {
        "logs": rows,
        "summary": {
            "total": len(rows),
            "unique_visitors": unique_visitors,
            "unique_sessions": unique_sessions,
            "unique_paths": unique_paths,
        },
        "filters": {
            "q": q.strip(),
            "visitor_id": visitor_id.strip(),
            "limit": normalized_limit,
        },
    }
