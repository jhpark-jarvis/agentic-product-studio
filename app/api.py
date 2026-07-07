from __future__ import annotations

from flask import Blueprint, jsonify, request

from .constants import DOCUMENT_TYPES, TASK_PRIORITIES, TASK_STATUSES
from .repositories.provider import get_repository_provider
from .utils import (
    WBS_PLATFORM_OPTIONS,
    build_pagination,
    markdown_to_html,
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
