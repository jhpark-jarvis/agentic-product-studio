from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.constants import SCHEDULE_TYPES
from app.utils import month_bounds, parse_date, parse_int, today_local, week_bounds

from ..dependencies import get_repository_provider, get_runtime_sqlite_db
from ..helpers import serialize_rows


router = APIRouter(prefix="/api/schedules", tags=["schedules"])


def _build_schedule_month_days(schedules, month_start, month_end, today):
    per_day = {}
    for item in schedules:
        start = parse_date(item["start_date"])
        end = parse_date(item["end_date"]) or start
        if not start or not end:
            continue
        if end < month_start or start > month_end:
            continue

        cursor = max(start, month_start)
        final = min(end, month_end)
        while cursor <= final:
            per_day.setdefault(cursor.isoformat(), []).append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "summary": item["description"] or "",
                    "schedule_type": item["schedule_type"],
                    "assignee_name": item["assignee_name"] or "-",
                    "task_title": item["task_title"] or "",
                    "start_date": item["start_date"],
                    "end_date": item["end_date"],
                    "starts_today": cursor == start,
                }
            )
            cursor += timedelta(days=1)

    ordered_days = []
    cursor = month_start
    while cursor <= month_end:
        day_items = per_day.get(cursor.isoformat(), [])
        start_items = [item for item in day_items if item["starts_today"]][:2]
        total_start_count = len([item for item in day_items if item["starts_today"]])
        continuing_count = sum(1 for item in day_items if not item["starts_today"])
        ordered_days.append(
            {
                "date": cursor.isoformat(),
                "is_today": cursor.isoformat() == today.isoformat(),
                "item_count": len(day_items),
                "start_items": start_items,
                "continuing_count": continuing_count,
                "hidden_start_count": max(0, total_start_count - len(start_items)),
                "modal_items": day_items,
            }
        )
        cursor += timedelta(days=1)
    return ordered_days


def _schedule_form_payload(payload):
    return {
        "title": (payload.get("title") or "").strip(),
        "description": (payload.get("description") or "").strip(),
        "start_date": payload.get("start_date") or None,
        "end_date": payload.get("end_date") or None,
        "assignee_id": payload.get("assignee_id") or None,
        "wbs_task_id": payload.get("wbs_task_id") or None,
        "schedule_type": (payload.get("schedule_type") or SCHEDULE_TYPES[0]).strip(),
    }


def _validate_schedule_payload(data):
    errors = []
    if not data["title"]:
        errors.append("일정 제목은 필수입니다.")
    if data["schedule_type"] not in SCHEDULE_TYPES:
        errors.append("유효하지 않은 일정 유형입니다.")

    start = parse_date(data["start_date"])
    end = parse_date(data["end_date"])
    if data["start_date"] and not start:
        errors.append("시작일 형식이 올바르지 않습니다.")
    if data["end_date"] and not end:
        errors.append("종료일 형식이 올바르지 않습니다.")
    if start and end and end < start:
        errors.append("종료일은 시작일보다 빠를 수 없습니다.")
    if data["assignee_id"] and not str(data["assignee_id"]).isdigit():
        errors.append("유효하지 않은 담당자입니다.")
    if data["wbs_task_id"] and not str(data["wbs_task_id"]).isdigit():
        errors.append("유효하지 않은 WBS 작업입니다.")
    return errors


@router.get("")
async def schedules_list(
    month: str = "",
    provider=Depends(get_repository_provider),
):
    today = today_local()
    week_start, week_end = week_bounds(today)

    month_query = month.strip() or today.strftime("%Y-%m")
    try:
        month_reference = datetime.strptime(month_query + "-01", "%Y-%m-%d").date()
    except ValueError:
        month_reference = today.replace(day=1)
        month_query = month_reference.strftime("%Y-%m")

    month_start, month_end = month_bounds(month_reference)
    schedules = provider.schedules.list_schedules()

    week_items = []
    for item in schedules:
        start = parse_date(item["start_date"])
        end = parse_date(item["end_date"]) or start
        if not start:
            continue
        if end >= week_start and start <= week_end:
            week_items.append(dict(item))

    return {
        "month_query": month_query,
        "week_range": {
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
        },
        "month_range": {
            "start": month_start.isoformat(),
            "end": month_end.isoformat(),
        },
        "week_items": week_items,
        "month_days": _build_schedule_month_days(schedules, month_start, month_end, today),
        "schedules": serialize_rows(schedules),
    }


@router.get("/editor")
async def schedule_editor_bootstrap(
    schedule_id: int = Query(default=0),
    provider=Depends(get_repository_provider),
):
    normalized_schedule_id = parse_int(schedule_id, default=0, minimum=0)
    schedule = None
    if normalized_schedule_id:
        schedule = provider.schedules.fetch_schedule(normalized_schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

    return {
        "schedule": dict(schedule) if schedule else None,
        "schedule_types": list(SCHEDULE_TYPES),
        "members": serialize_rows(provider.common.fetch_active_members()),
        "tasks": serialize_rows(provider.common.fetch_task_link_options()),
    }


@router.post("")
async def create_schedule_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    data = _schedule_form_payload(payload)
    errors = _validate_schedule_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    schedule_id = provider.schedules.create_schedule(data)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "schedule_id": schedule_id,
        "redirect_path": "/schedules",
    }


@router.post("/{schedule_id}")
async def update_schedule_api(
    schedule_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    schedule = provider.schedules.fetch_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    data = _schedule_form_payload(payload)
    errors = _validate_schedule_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    provider.schedules.update_schedule(schedule_id, data)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "schedule_id": schedule_id,
        "redirect_path": "/schedules",
    }


@router.delete("/{schedule_id}")
async def delete_schedule_api(
    schedule_id: int,
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    schedule = provider.schedules.fetch_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    provider.schedules.delete_schedule(schedule_id)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {"deleted": True, "redirect_path": "/schedules"}
