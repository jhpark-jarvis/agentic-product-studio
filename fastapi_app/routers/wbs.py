from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.constants import TASK_PRIORITIES, TASK_STATUSES
from app.utils import parse_date, parse_int, today_local
from app.utils import WBS_PLATFORM_OPTIONS

from ..dependencies import get_repository_provider, get_runtime_sqlite_db
from ..helpers import serialize_rows


router = APIRouter(prefix="/api/wbs", tags=["wbs"])


def _is_completed_task(task) -> bool:
    completed_status = TASK_STATUSES[3] if len(TASK_STATUSES) > 3 else "완료"
    status = (task["status"] or "").strip()
    completed_date = parse_date(task["completed_date"])
    progress = task["progress"] or 0
    return status == completed_status or completed_date is not None or progress >= 100


def _flatten_wbs_tasks(provider, filters: dict[str, str]):
    tasks = provider.wbs.fetch_tasks_for_filters(filters)

    children: dict[int | None, list] = {}
    by_id = {task["id"]: task for task in tasks}
    for task in tasks:
        parent_id = task["parent_id"] if task["parent_id"] in by_id else None
        children.setdefault(parent_id, []).append(task)

    today = today_local()
    rows = []

    def walk(parent_id: int | None, depth: int):
        for task in children.get(parent_id, []):
            due = parse_date(task["due_date"])
            completed = _is_completed_task(task)
            is_delayed = bool(due and due < today and not completed)
            is_due_soon = bool(due and 0 <= (due - today).days <= 3 and not completed)
            rows.append(
                {
                    "task": dict(task),
                    "depth": depth,
                    "is_delayed": is_delayed,
                    "is_due_soon": is_due_soon,
                }
            )
            walk(task["id"], depth + 1)

    walk(None, 0)
    return rows


def _task_form_payload(payload: dict[str, Any]):
    document_ids = payload.get("document_ids") or []
    normalized_document_ids = []
    for value in document_ids:
        if isinstance(value, int):
            normalized_document_ids.append(value)
        elif isinstance(value, str) and value.isdigit():
            normalized_document_ids.append(int(value))

    return {
        "parent_id": payload.get("parent_id") or None,
        "title": (payload.get("title") or "").strip(),
        "description": (payload.get("description") or "").strip(),
        "assignee_id": payload.get("assignee_id") or None,
        "platform": (payload.get("platform") or WBS_PLATFORM_OPTIONS[0]).strip(),
        "status": (payload.get("status") or TASK_STATUSES[0]).strip(),
        "priority": (payload.get("priority") or TASK_PRIORITIES[1]).strip(),
        "start_date": payload.get("start_date") or None,
        "due_date": payload.get("due_date") or None,
        "completed_date": payload.get("completed_date") or None,
        "progress": str(payload.get("progress") or "0").strip() or "0",
        "notes": (payload.get("notes") or "").strip(),
        "document_ids": normalized_document_ids,
    }


def _validate_task_payload(data, task_id: int | None = None):
    errors = []
    if not data["title"]:
        errors.append("작업명은 필수입니다.")
    if data["status"] not in TASK_STATUSES:
        errors.append("유효하지 않은 상태값입니다.")
    if data["priority"] not in TASK_PRIORITIES:
        errors.append("유효하지 않은 우선순위입니다.")
    if data["platform"] not in WBS_PLATFORM_OPTIONS:
        errors.append("유효하지 않은 플랫폼입니다.")

    try:
        progress_value = int(data["progress"])
        if not 0 <= progress_value <= 100:
            raise ValueError
    except ValueError:
        errors.append("진행률은 0에서 100 사이 정수여야 합니다.")
        progress_value = 0

    completed_status = TASK_STATUSES[3] if len(TASK_STATUSES) > 3 else "완료"
    if data["status"] == completed_status:
        progress_value = 100
        if not data["completed_date"]:
            data["completed_date"] = today_local().isoformat()

    data["progress"] = progress_value

    if data["parent_id"] and not str(data["parent_id"]).isdigit():
        errors.append("유효하지 않은 상위 작업입니다.")
    if data["assignee_id"] and not str(data["assignee_id"]).isdigit():
        errors.append("유효하지 않은 담당자입니다.")
    if data["parent_id"] and task_id and int(data["parent_id"]) == task_id:
        errors.append("상위 작업으로 자기 자신을 선택할 수 없습니다.")

    start = parse_date(data["start_date"])
    due = parse_date(data["due_date"])
    done = parse_date(data["completed_date"])
    if data["start_date"] and not start:
        errors.append("시작일 형식이 올바르지 않습니다.")
    if data["due_date"] and not due:
        errors.append("종료 예정일 형식이 올바르지 않습니다.")
    if data["completed_date"] and not done:
        errors.append("실제 완료일 형식이 올바르지 않습니다.")
    if start and due and start > due:
        errors.append("시작일은 종료 예정일보다 늦을 수 없습니다.")

    return errors


@router.get("")
async def wbs_list(
    status: str = "",
    assignee_id: str = "",
    priority: str = "",
    platform: str = "",
    provider=Depends(get_repository_provider),
):
    filters = {
        "status": status.strip(),
        "assignee_id": assignee_id.strip(),
        "priority": priority.strip(),
        "platform": platform.strip(),
    }

    return {
        "task_rows": _flatten_wbs_tasks(provider, filters),
        "members": serialize_rows(provider.common.fetch_active_members()),
        "statuses": list(TASK_STATUSES),
        "priorities": list(TASK_PRIORITIES),
        "platforms": list(WBS_PLATFORM_OPTIONS),
        "filters": filters,
    }


@router.get("/editor")
async def wbs_editor_bootstrap(
    task_id: int = Query(default=0),
    provider=Depends(get_repository_provider),
):
    normalized_task_id = parse_int(task_id, default=0, minimum=0)
    task = None
    selected_document_ids = []
    if normalized_task_id:
        task, selected_document_ids = provider.wbs.fetch_task_with_links(normalized_task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task": dict(task) if task else None,
        "selected_document_ids": list(selected_document_ids),
        "members": serialize_rows(provider.common.fetch_active_members()),
        "parent_tasks": serialize_rows(
            provider.common.fetch_parent_task_options(
                exclude_task_id=normalized_task_id if normalized_task_id else None
            )
        ),
        "documents": serialize_rows(provider.common.fetch_document_link_options()),
        "statuses": list(TASK_STATUSES),
        "priorities": list(TASK_PRIORITIES),
        "platforms": list(WBS_PLATFORM_OPTIONS),
    }


@router.get("/{task_id}")
async def wbs_detail(task_id: int, provider=Depends(get_repository_provider)):
    task, selected_document_ids = provider.wbs.fetch_task_with_links(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    document_options = serialize_rows(provider.common.fetch_document_link_options())
    linked_documents = [
        document for document in document_options if document["id"] in set(selected_document_ids)
    ]

    return {
        "task": dict(task),
        "linked_documents": linked_documents,
        "document_ids": list(selected_document_ids),
        "is_completed": _is_completed_task(task),
    }


@router.post("")
async def create_wbs_task_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    data = _task_form_payload(payload)
    errors = _validate_task_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    task_id = provider.wbs.create_task(data)
    provider.wbs.sync_task_documents(task_id, data["document_ids"])
    if sqlite_db is not None:
        sqlite_db.commit()

    return {"task_id": task_id, "redirect_path": "/wbs"}


@router.post("/{task_id}")
async def update_wbs_task_api(
    task_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    existing_task, _selected_document_ids = provider.wbs.fetch_task_with_links(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = _task_form_payload(payload)
    errors = _validate_task_payload(data, task_id=task_id)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    provider.wbs.update_task(task_id, data)
    provider.wbs.sync_task_documents(task_id, data["document_ids"])
    if sqlite_db is not None:
        sqlite_db.commit()

    return {"task_id": task_id, "redirect_path": "/wbs"}


@router.delete("/{task_id}")
async def delete_wbs_task_api(
    task_id: int,
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    existing_task, _selected_document_ids = provider.wbs.fetch_task_with_links(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    provider.wbs.delete_task(task_id)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {"deleted": True, "redirect_path": "/wbs"}
