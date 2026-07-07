from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from uuid import uuid4

from flask import Blueprint, jsonify, request

from .constants import DOCUMENT_TYPES, SCHEDULE_TYPES, TASK_PRIORITIES, TASK_STATUSES
from .db import get_db
from .repositories.provider import get_repository_provider
from .utils import (
    WBS_PLATFORM_OPTIONS,
    build_pagination,
    markdown_to_html,
    month_bounds,
    parse_date,
    parse_int,
    today_local,
    week_bounds,
)


bp = Blueprint("api", __name__, url_prefix="/api")
PER_PAGE_OPTIONS = (10, 20, 50, 100)


def _serialize_rows(rows):
    return [dict(row) for row in rows]


def _is_completed_task(task) -> bool:
    completed_status = TASK_STATUSES[3] if len(TASK_STATUSES) > 3 else "완료"
    status = (task["status"] or "").strip()
    completed_date = parse_date(task["completed_date"])
    progress = task["progress"] or 0
    return status == completed_status or completed_date is not None or progress >= 100


def _flatten_wbs_tasks(filters: dict[str, str]):
    tasks = get_repository_provider().wbs.fetch_tasks_for_filters(filters)

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


def _build_schedule_month_days(schedules, month_start, month_end, today):
    per_day = defaultdict(list)
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
            per_day[cursor.isoformat()].append(
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


def _document_form_payload(payload: dict):
    related_task_ids = payload.get("related_task_ids") or []
    normalized_task_ids = []
    for value in related_task_ids:
        if isinstance(value, int):
            normalized_task_ids.append(value)
        elif isinstance(value, str) and value.isdigit():
            normalized_task_ids.append(int(value))

    return {
        "asset_draft_key": (payload.get("asset_draft_key") or "").strip(),
        "title": (payload.get("title") or "").strip(),
        "doc_type": (payload.get("doc_type") or DOCUMENT_TYPES[-1]).strip(),
        "folder_id": payload.get("folder_id") or None,
        "new_folder_name": (payload.get("new_folder_name") or "").strip(),
        "content": (payload.get("content") or "").strip(),
        "author_id": payload.get("author_id") or None,
        "tags": (payload.get("tags") or "").strip(),
        "is_hidden": 1 if payload.get("is_hidden") else 0,
        "related_task_ids": normalized_task_ids,
    }


def _validate_document_payload(data):
    errors = []
    if not data["title"]:
        errors.append("문서 제목은 필수입니다.")
    if data["doc_type"] not in DOCUMENT_TYPES:
        errors.append("유효하지 않은 문서 유형입니다.")
    if not data["content"]:
        errors.append("문서 내용을 입력해주세요.")
    if data["folder_id"] and not str(data["folder_id"]).isdigit():
        errors.append("유효하지 않은 폴더입니다.")
    return errors


def _resolve_document_folder_id(data):
    if data["new_folder_name"]:
        return get_repository_provider().documents.ensure_folder(
            data["doc_type"], data["new_folder_name"]
        )
    if data["folder_id"]:
        return int(data["folder_id"])
    return None


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


@bp.route("/documents")
def documents_list():
    search = request.args.get("q", "").strip()
    doc_type = request.args.get("doc_type", "").strip()
    tag = request.args.get("tag", "").strip()
    folder_id = request.args.get("folder_id", "").strip()
    page = parse_int(request.args.get("page"), default=1, minimum=1)
    per_page = parse_int(request.args.get("per_page"), default=20, allowed=set(PER_PAGE_OPTIONS))

    total_count, documents = get_repository_provider().documents.list_documents(
        search=search,
        doc_type=doc_type,
        tag=tag,
        folder_id=folder_id,
        limit=per_page,
        offset=max((page - 1) * per_page, 0),
    )
    pagination = build_pagination(page, per_page, total_count)
    folder_options = get_repository_provider().documents.fetch_document_folders(doc_type or None)
    tag_options = get_repository_provider().documents.fetch_tag_options()

    return jsonify(
        {
            "documents": _serialize_rows(documents),
            "document_types": list(DOCUMENT_TYPES),
            "folder_options": _serialize_rows(folder_options),
            "tag_options": _serialize_rows(tag_options),
            "pagination": pagination,
            "per_page_options": list(PER_PAGE_OPTIONS),
            "filters": {
                "q": search,
                "doc_type": doc_type,
                "tag": tag,
                "folder_id": folder_id,
            },
        }
    )


@bp.route("/documents/<int:document_id>")
def document_detail(document_id: int):
    document, related_tasks, tags = get_repository_provider().documents.fetch_document_with_relations(
        document_id
    )
    if not document:
        return jsonify({"error": "Document not found"}), 404

    assets = get_repository_provider().documents.fetch_document_assets(document_id)
    content = document["content"] or ""

    return jsonify(
        {
            "document": dict(document),
            "related_tasks": _serialize_rows(related_tasks),
            "tags": list(tags),
            "assets": _serialize_rows(assets),
            "rendered_content": str(markdown_to_html(content)),
            "word_count": len(content.split()),
            "heading_count": sum(
                1 for line in content.splitlines() if line.lstrip().startswith("#")
            ),
        }
    )


@bp.route("/documents/editor")
def document_editor_bootstrap():
    document_id = parse_int(request.args.get("document_id"), default=0, minimum=0)
    document = None
    related_tasks = []
    tags = []
    assets = []

    if document_id:
        document, related_tasks, tags = (
            get_repository_provider().documents.fetch_document_with_relations(document_id)
        )
        if not document:
            return jsonify({"error": "Document not found"}), 404
        assets = get_repository_provider().documents.fetch_document_assets(document_id)

    selected_type = (
        document["doc_type"] if document else DOCUMENT_TYPES[0]
    )

    return jsonify(
        {
            "document": dict(document) if document else None,
            "document_types": list(DOCUMENT_TYPES),
            "document_folders": _serialize_rows(
                get_repository_provider().documents.fetch_document_folders()
            ),
            "members": _serialize_rows(
                get_repository_provider().common.fetch_active_members()
            ),
            "tasks": _serialize_rows(
                get_repository_provider().common.fetch_task_link_options()
            ),
            "related_task_ids": [task["id"] for task in related_tasks],
            "tags": list(tags),
            "assets": _serialize_rows(assets),
            "selected_type": selected_type,
            "asset_draft_key": "" if document else uuid4().hex,
        }
    )


@bp.route("/documents", methods=["POST"])
def create_document_api():
    data = _document_form_payload(request.get_json(silent=True) or {})
    errors = _validate_document_payload(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    folder_id = _resolve_document_folder_id(data)
    document_id = get_repository_provider().documents.create_document(data, folder_id)
    if data["asset_draft_key"]:
        get_repository_provider().documents.assign_draft_assets(
            document_id, data["asset_draft_key"]
        )
    get_repository_provider().documents.sync_document_tags(document_id, data["tags"])
    get_repository_provider().documents.sync_task_documents(
        document_id, data["related_task_ids"]
    )
    db.commit()

    return jsonify(
        {
            "document_id": document_id,
            "redirect_path": f"/app/documents/{document_id}",
        }
    )


@bp.route("/documents/<int:document_id>", methods=["POST"])
def update_document_api(document_id: int):
    existing_document, _related_tasks, _tags = (
        get_repository_provider().documents.fetch_document_with_relations(document_id)
    )
    if not existing_document:
        return jsonify({"error": "Document not found"}), 404

    data = _document_form_payload(request.get_json(silent=True) or {})
    errors = _validate_document_payload(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    folder_id = _resolve_document_folder_id(data)
    get_repository_provider().documents.update_document(document_id, data, folder_id)
    get_repository_provider().documents.sync_document_tags(document_id, data["tags"])
    get_repository_provider().documents.sync_task_documents(
        document_id, data["related_task_ids"]
    )
    db.commit()

    return jsonify(
        {
            "document_id": document_id,
            "redirect_path": f"/app/documents/{document_id}",
        }
    )


@bp.route("/schedules")
def schedules_list():
    today = today_local()
    week_start, week_end = week_bounds(today)

    month_query = request.args.get("month", today.strftime("%Y-%m")).strip()
    try:
        month_reference = datetime.strptime(month_query + "-01", "%Y-%m-%d").date()
    except ValueError:
        month_reference = today.replace(day=1)
        month_query = month_reference.strftime("%Y-%m")

    month_start, month_end = month_bounds(month_reference)
    schedules = get_repository_provider().schedules.list_schedules()

    week_items = []
    for item in schedules:
        start = parse_date(item["start_date"])
        end = parse_date(item["end_date"]) or start
        if not start:
            continue
        if end >= week_start and start <= week_end:
            week_items.append(dict(item))

    return jsonify(
        {
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
            "month_days": _build_schedule_month_days(
                schedules, month_start, month_end, today
            ),
            "schedules": _serialize_rows(schedules),
        }
    )


@bp.route("/schedules/editor")
def schedule_editor_bootstrap():
    schedule_id = parse_int(request.args.get("schedule_id"), default=0, minimum=0)
    schedule = None
    if schedule_id:
        schedule = get_repository_provider().schedules.fetch_schedule(schedule_id)
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404

    return jsonify(
        {
            "schedule": dict(schedule) if schedule else None,
            "schedule_types": list(SCHEDULE_TYPES),
            "members": _serialize_rows(get_repository_provider().common.fetch_active_members()),
            "tasks": _serialize_rows(get_repository_provider().common.fetch_task_link_options()),
        }
    )


@bp.route("/schedules", methods=["POST"])
def create_schedule_api():
    data = _schedule_form_payload(request.get_json(silent=True) or {})
    errors = _validate_schedule_payload(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    schedule_id = get_repository_provider().schedules.create_schedule(data)
    db.commit()

    return jsonify(
        {
            "schedule_id": schedule_id,
            "redirect_path": "/app/schedules",
        }
    )


@bp.route("/schedules/<int:schedule_id>", methods=["POST"])
def update_schedule_api(schedule_id: int):
    schedule = get_repository_provider().schedules.fetch_schedule(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    data = _schedule_form_payload(request.get_json(silent=True) or {})
    errors = _validate_schedule_payload(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    get_repository_provider().schedules.update_schedule(schedule_id, data)
    db.commit()

    return jsonify(
        {
            "schedule_id": schedule_id,
            "redirect_path": "/app/schedules",
        }
    )


@bp.route("/schedules/<int:schedule_id>", methods=["DELETE"])
def delete_schedule_api(schedule_id: int):
    schedule = get_repository_provider().schedules.fetch_schedule(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    db = get_db()
    get_repository_provider().schedules.delete_schedule(schedule_id)
    db.commit()

    return jsonify({"deleted": True, "redirect_path": "/app/schedules"})


@bp.route("/dashboard")
def dashboard_summary():
    today = today_local()
    _, week_end = week_bounds(today)
    today_str = today.isoformat()
    week_end_str = week_end.isoformat()

    dashboard = get_repository_provider().dashboard
    summary = dashboard.fetch_dashboard_summary(today_str)
    week_due_tasks = dashboard.fetch_week_due_tasks(today_str, week_end_str)
    recent_documents = dashboard.fetch_recent_documents()
    recent_tasks = dashboard.fetch_recent_tasks()
    pinned_notice = dashboard.fetch_pinned_notice()
    upcoming_schedules = dashboard.fetch_upcoming_schedules(today_str)

    return jsonify(
        {
            "summary": dict(summary) if summary else {},
            "week_due_tasks": _serialize_rows(week_due_tasks),
            "recent_documents": _serialize_rows(recent_documents),
            "recent_tasks": _serialize_rows(recent_tasks),
            "pinned_notice": dict(pinned_notice) if pinned_notice else None,
            "upcoming_schedules": _serialize_rows(upcoming_schedules),
            "today": today_str,
            "week_end": week_end_str,
        }
    )


@bp.route("/wbs")
def wbs_list():
    filters = {
        "status": request.args.get("status", "").strip(),
        "assignee_id": request.args.get("assignee_id", "").strip(),
        "priority": request.args.get("priority", "").strip(),
        "platform": request.args.get("platform", "").strip(),
    }

    return jsonify(
        {
            "task_rows": _flatten_wbs_tasks(filters),
            "members": _serialize_rows(get_repository_provider().common.fetch_active_members()),
            "statuses": list(TASK_STATUSES),
            "priorities": list(TASK_PRIORITIES),
            "platforms": list(WBS_PLATFORM_OPTIONS),
            "filters": filters,
        }
    )


@bp.route("/members")
def members_list():
    members = get_repository_provider().members.list_members()
    return jsonify(
        {
            "members": _serialize_rows(members),
        }
    )
