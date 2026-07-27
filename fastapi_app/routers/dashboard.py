from __future__ import annotations

from fastapi import APIRouter, Depends

from app.utils import today_local, week_bounds

from ..dependencies import get_repository_provider
from ..helpers import serialize_rows


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def dashboard_summary(provider=Depends(get_repository_provider)):
    today = today_local()
    week_start, week_end = week_bounds(today)
    today_str = today.isoformat()
    week_start_str = week_start.isoformat()
    week_end_str = week_end.isoformat()

    dashboard = provider.dashboard
    summary = dashboard.fetch_dashboard_summary(today_str)
    week_due_tasks = dashboard.fetch_week_due_tasks(today_str, week_end_str)
    recent_documents = dashboard.fetch_recent_documents()
    recent_tasks = dashboard.fetch_recent_tasks()
    pinned_notice = dashboard.fetch_pinned_notice()
    upcoming_schedules = dashboard.fetch_upcoming_schedules(today_str)

    return {
        "summary": dict(summary) if summary else {},
        "week_due_tasks": serialize_rows(week_due_tasks),
        "recent_documents": serialize_rows(recent_documents),
        "recent_tasks": serialize_rows(recent_tasks),
        "pinned_notice": dict(pinned_notice) if pinned_notice else None,
        "upcoming_schedules": serialize_rows(upcoming_schedules),
        "today": today_str,
        "week_start": week_start_str,
        "week_end": week_end_str,
    }
