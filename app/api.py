from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request

from .constants import ASSET_STATUSES, ASSET_TYPES, DOCUMENT_TYPES, SCHEDULE_TYPES, TASK_PRIORITIES, TASK_STATUSES
from .db import get_db
from .page_view_logging import read_page_view_logs, write_page_view_log
from .repositories.assets import AssetGroupError
from .repositories.provider import get_repository_provider
from .storage import delete_object, upload_file
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


def _client_ip() -> str:
    forwarded_for = (request.headers.get("X-Forwarded-For") or "").strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or request.remote_addr or ""


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


def _member_form_payload(payload):
    return {
        "name": (payload.get("name") or "").strip(),
        "role": (payload.get("role") or "").strip(),
        "part": (payload.get("part") or "").strip(),
        "contact": (payload.get("contact") or "").strip(),
        "is_active": 1 if payload.get("is_active") else 0,
    }


def _validate_member_payload(data):
    errors = []
    if not data["name"]:
        errors.append("팀원 이름은 필수입니다.")
    return errors


def _asset_form_payload(payload, *, uploaded=None, existing=None):
    existing_data = dict(existing) if existing else {}
    return {
        "title": (payload.get("title") or "").strip(),
        "asset_type": (payload.get("asset_type") or "").strip(),
        "category": (payload.get("category") or "").strip(),
        "tags": (payload.get("tags") or "").strip(),
        "status": (payload.get("status") or ASSET_STATUSES[0]).strip(),
        "is_hidden": 1 if payload.get("is_hidden") else 0,
        "created_by": payload.get("created_by") or None,
        "notes": (payload.get("notes") or "").strip(),
        "file_name": uploaded["file_name"] if uploaded else existing_data.get("file_name", ""),
        "original_filename": uploaded["original_filename"] if uploaded else existing_data.get("original_filename", ""),
        "object_key": uploaded["object_key"] if uploaded else existing_data.get("object_key", ""),
        "url": uploaded["url"] if uploaded else existing_data.get("url", ""),
        "content_type": uploaded["content_type"] if uploaded else existing_data.get("content_type", ""),
        "size": int(uploaded["size"]) if uploaded else int(existing_data.get("size") or 0),
        "checksum": uploaded["checksum"] if uploaded else existing_data.get("checksum", ""),
    }


def _asset_type_options():
    repository_options = [
        row["asset_type"]
        for row in get_repository_provider().assets.fetch_asset_type_options()
        if (row.get("asset_type") or "").strip()
    ]
    merged = []
    for option in [*ASSET_TYPES, *repository_options]:
        normalized = (option or "").strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def _build_asset_group_tree(rows):
    nodes_by_path: dict[str, dict] = {}
    roots: list[dict] = []

    for row in rows:
        path = str(row.get("path") or "").strip()
        if not path:
            continue
        node = {
            "path": path,
            "name": path.split("/")[-1],
            "direct_asset_count": int(row.get("direct_asset_count") or 0),
            "total_asset_count": int(row.get("direct_asset_count") or 0),
            "last_updated_at": row.get("last_updated_at"),
            "is_explicit": bool(row.get("is_explicit")),
            "children": [],
        }
        nodes_by_path[path] = node

    for path in sorted(nodes_by_path.keys(), key=lambda value: (value.count("/"), value.lower())):
        node = nodes_by_path[path]
        parent_path = "/".join(path.split("/")[:-1])
        parent = nodes_by_path.get(parent_path)
        if parent:
            parent["children"].append(node)
        else:
            roots.append(node)

    def accumulate(node: dict):
        total = node["direct_asset_count"]
        for child in node["children"]:
            total += accumulate(child)
        node["total_asset_count"] = total
        node["children"].sort(key=lambda item: item["name"].lower())
        return total

    for root in roots:
        accumulate(root)
    roots.sort(key=lambda item: item["name"].lower())
    return roots


def _asset_group_payload(*, include_hidden: bool):
    group_rows = get_repository_provider().assets.fetch_asset_groups(include_hidden=include_hidden)
    category_rows = get_repository_provider().assets.fetch_category_options(include_hidden=include_hidden)
    ungrouped_count = 0
    for row in category_rows:
        if row.get("category") == "미분류":
            ungrouped_count = int(row.get("asset_count") or 0)
            break
    return {
        "tree": _build_asset_group_tree(group_rows),
        "ungrouped_asset_count": ungrouped_count,
    }


def _validate_asset_payload(data, *, require_file: bool):
    errors = []
    if not data["title"]:
        errors.append("Asset 제목은 필수입니다.")
    if data["status"] not in ASSET_STATUSES:
        errors.append("유효하지 않은 Asset 상태입니다.")
    if require_file and not data["object_key"]:
        errors.append("업로드할 파일은 필수입니다.")
    if data["created_by"] and not str(data["created_by"]).isdigit():
        errors.append("유효하지 않은 등록자입니다.")
    return errors


def _task_form_payload(payload):
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


@bp.route("/documents")
def documents_list():
    search = request.args.get("q", "").strip()
    doc_type = request.args.get("doc_type", "").strip()
    tag = request.args.get("tag", "").strip()
    folder_id = request.args.get("folder_id", "").strip()
    include_hidden = request.args.get("include_hidden", "").strip() in {"1", "true", "yes", "on"}
    page = parse_int(request.args.get("page"), default=1, minimum=1)
    per_page = parse_int(request.args.get("per_page"), default=20, allowed=set(PER_PAGE_OPTIONS))

    total_count, documents = get_repository_provider().documents.list_documents(
        search=search,
        doc_type=doc_type,
        tag=tag,
        folder_id=folder_id,
        include_hidden=include_hidden,
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
                "include_hidden": include_hidden,
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
            "redirect_path": f"/documents/{document_id}",
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
            "redirect_path": f"/documents/{document_id}",
        }
    )


@bp.route("/documents/<int:document_id>", methods=["DELETE"])
def delete_document_api(document_id: int):
    existing_document, _related_tasks, _tags = (
        get_repository_provider().documents.fetch_document_with_relations(document_id)
    )
    if not existing_document:
        return jsonify({"error": "Document not found"}), 404

    db = get_db()
    assets = get_repository_provider().documents.fetch_document_assets(document_id)
    for asset in assets:
        delete_object(dict(asset).get("object_key") or "")
    get_repository_provider().documents.delete_document(document_id)
    db.commit()

    return jsonify(
        {
            "deleted": True,
            "redirect_path": "/documents",
        }
    )


@bp.route("/documents/<int:document_id>/assets/<int:asset_id>", methods=["DELETE"])
def delete_document_asset_api(document_id: int, asset_id: int):
    existing_document, _related_tasks, _tags = (
        get_repository_provider().documents.fetch_document_with_relations(document_id)
    )
    if not existing_document:
        return jsonify({"error": "Document not found"}), 404

    asset = get_repository_provider().documents.fetch_document_asset(asset_id)
    if not asset or int(asset["document_id"] or 0) != document_id:
        return jsonify({"error": "Document asset not found"}), 404

    db = get_db()
    delete_object(dict(asset).get("object_key") or "")
    get_repository_provider().documents.delete_document_asset(asset_id)
    db.commit()

    return jsonify(
        {
            "deleted": True,
            "asset_id": asset_id,
            "document_id": document_id,
        }
    )


@bp.route("/assets")
def assets_list():
    search = request.args.get("q", "").strip()
    asset_type = request.args.get("asset_type", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    tag = request.args.get("tag", "").strip()
    updated_since = request.args.get("updated_since", "").strip()
    include_hidden = request.args.get("include_hidden", "").strip() in {"1", "true", "yes", "on"}
    page = parse_int(request.args.get("page"), default=1, minimum=1)
    per_page = parse_int(request.args.get("per_page"), default=20, allowed=set(PER_PAGE_OPTIONS))

    total_count, assets = get_repository_provider().assets.list_assets(
        search=search,
        asset_type=asset_type,
        category=category,
        status=status,
        tag=tag,
        include_hidden=include_hidden,
        updated_since=updated_since,
        limit=per_page,
        offset=max((page - 1) * per_page, 0),
    )
    pagination = build_pagination(page, per_page, total_count)

    return jsonify(
        {
            "assets": _serialize_rows(assets),
            "statuses": list(ASSET_STATUSES),
            "asset_type_options": _asset_type_options(),
            "category_options": _serialize_rows(
                get_repository_provider().assets.fetch_category_options(include_hidden=include_hidden)
            ),
            "group_browser": _asset_group_payload(include_hidden=include_hidden),
            "tag_options": _serialize_rows(get_repository_provider().assets.fetch_tag_options()),
            "pagination": pagination,
            "per_page_options": list(PER_PAGE_OPTIONS),
            "filters": {
                "q": search,
                "asset_type": asset_type,
                "category": category,
                "status": status,
                "tag": tag,
                "updated_since": updated_since,
                "include_hidden": include_hidden,
            },
        }
    )


@bp.route("/assets/<int:asset_id>")
def asset_detail(asset_id: int):
    asset, tags = get_repository_provider().assets.fetch_asset_with_tags(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
    return jsonify(
        {
            "asset": dict(asset),
            "tags": list(tags),
            "is_image": str(dict(asset).get("content_type") or "").startswith("image/"),
        }
    )


@bp.route("/assets/editor")
def asset_editor_bootstrap():
    asset_id = parse_int(request.args.get("asset_id"), default=0, minimum=0)
    asset = None
    tags = []
    if asset_id:
        asset, tags = get_repository_provider().assets.fetch_asset_with_tags(asset_id)
        if not asset:
            return jsonify({"error": "Asset not found"}), 404

    return jsonify(
        {
            "asset": dict(asset) if asset else None,
            "tags": list(tags),
            "statuses": list(ASSET_STATUSES),
            "asset_type_options": _asset_type_options(),
            "members": _serialize_rows(get_repository_provider().common.fetch_active_members()),
            "group_browser": _asset_group_payload(include_hidden=True),
        }
    )


@bp.route("/assets/groups")
def asset_group_list_api():
    include_hidden = request.args.get("include_hidden", "").strip() in {"1", "true", "yes", "on"}
    return jsonify(_asset_group_payload(include_hidden=include_hidden))


@bp.route("/assets/groups", methods=["POST"])
def create_asset_group_api():
    payload = request.get_json(silent=True) or {}
    parent_path = str(payload.get("parent_path") or "").strip()
    name = str(payload.get("name") or "").strip()
    combined = "/".join(part for part in [parent_path, name] if part)
    if not name:
        return jsonify({"error": "새 폴더 이름을 입력해주세요."}), 400
    try:
        path = get_repository_provider().assets.create_asset_group(combined)
        get_db().commit()
    except AssetGroupError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(
        {
            "path": path,
            "group_browser": _asset_group_payload(include_hidden=True),
        }
    )


@bp.route("/assets/groups/rename", methods=["POST"])
def rename_asset_group_api():
    payload = request.get_json(silent=True) or {}
    path = str(payload.get("path") or "").strip()
    new_name = str(payload.get("new_name") or "").strip()
    if not new_name:
        return jsonify({"error": "변경할 폴더 이름을 입력해주세요."}), 400
    try:
        renamed_path = get_repository_provider().assets.rename_asset_group(path, new_name)
        get_db().commit()
    except AssetGroupError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(
        {
            "path": renamed_path,
            "group_browser": _asset_group_payload(include_hidden=True),
        }
    )


@bp.route("/assets/groups", methods=["DELETE"])
def delete_asset_group_api():
    payload = request.get_json(silent=True) or {}
    path = str(payload.get("path") or "").strip()
    try:
        get_repository_provider().assets.delete_asset_group(path)
        get_db().commit()
    except AssetGroupError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(
        {
            "deleted": True,
            "group_browser": _asset_group_payload(include_hidden=True),
        }
    )


@bp.route("/assets", methods=["POST"])
def create_asset_api():
    uploaded_file = request.files.get("file")
    uploaded = None
    if uploaded_file and uploaded_file.filename:
        stored = upload_file(uploaded_file, folder="assets")
        uploaded = {
            **stored,
            "file_name": uploaded_file.filename,
            "original_filename": uploaded_file.filename,
        }
    data = _asset_form_payload(request.form, uploaded=uploaded)
    errors = _validate_asset_payload(data, require_file=True)
    if errors:
        if uploaded:
            delete_object(uploaded["object_key"])
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    try:
        asset_id = get_repository_provider().assets.create_asset(data)
        db.commit()
    except Exception:
        if uploaded:
            delete_object(uploaded["object_key"])
        raise
    return jsonify({"asset_id": asset_id, "redirect_path": f"/assets/{asset_id}"})


@bp.route("/assets/<int:asset_id>", methods=["POST"])
def update_asset_api(asset_id: int):
    existing = get_repository_provider().assets.fetch_asset(asset_id)
    if not existing:
        return jsonify({"error": "Asset not found"}), 404

    uploaded_file = request.files.get("file")
    uploaded = None
    if uploaded_file and uploaded_file.filename:
        stored = upload_file(uploaded_file, folder="assets")
        uploaded = {
            **stored,
            "file_name": uploaded_file.filename,
            "original_filename": uploaded_file.filename,
        }

    data = _asset_form_payload(request.form, uploaded=uploaded, existing=existing)
    errors = _validate_asset_payload(data, require_file=False)
    if errors:
        if uploaded:
            delete_object(uploaded["object_key"])
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    try:
        get_repository_provider().assets.update_asset(asset_id, data)
        db.commit()
    except Exception:
        if uploaded:
            delete_object(uploaded["object_key"])
        raise
    existing_object_key = dict(existing).get("object_key") or ""
    if uploaded and existing_object_key and existing_object_key != data["object_key"]:
        delete_object(existing_object_key)
    return jsonify({"asset_id": asset_id, "redirect_path": f"/assets/{asset_id}"})


@bp.route("/assets/<int:asset_id>", methods=["DELETE"])
def delete_asset_api(asset_id: int):
    existing = get_repository_provider().assets.fetch_asset(asset_id)
    if not existing:
        return jsonify({"error": "Asset not found"}), 404
    db = get_db()
    get_repository_provider().assets.delete_asset(asset_id)
    db.commit()
    delete_object(dict(existing).get("object_key") or "")
    return jsonify({"deleted": True, "redirect_path": "/assets"})


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
            "redirect_path": "/schedules",
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
            "redirect_path": "/schedules",
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

    return jsonify({"deleted": True, "redirect_path": "/schedules"})


@bp.route("/dashboard")
def dashboard_summary():
    today = today_local()
    week_start, week_end = week_bounds(today)
    today_str = today.isoformat()
    week_start_str = week_start.isoformat()
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
            "week_start": week_start_str,
            "week_end": week_end_str,
        }
    )


@bp.route("/telemetry/page-view", methods=["POST"])
def track_page_view():
    payload = request.get_json(silent=True) or {}
    path = str(payload.get("path") or "").strip()
    referrer = str(payload.get("referrer") or "").strip()
    visitor_id = str(payload.get("visitor_id") or "").strip()
    session_id = str(payload.get("session_id") or "").strip()
    identity_type = str(payload.get("identity_type") or "anonymous_browser").strip()

    if not path.startswith("/"):
        return jsonify({"error": "Invalid path"}), 400
    if not visitor_id:
        return jsonify({"error": "Missing visitor_id"}), 400
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    write_page_view_log(
        current_app,
        {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "path": path,
            "referrer": referrer,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "identity_type": identity_type,
            "ip": _client_ip(),
            "user_agent": request.headers.get("User-Agent", ""),
        },
    )
    return jsonify({"logged": True})


@bp.route("/logs/page-views")
def page_view_logs():
    limit = parse_int(request.args.get("limit"), default=200, minimum=1)
    search = request.args.get("q", "").strip()
    visitor_id = request.args.get("visitor_id", "").strip()
    rows = read_page_view_logs(
        current_app,
        limit=min(limit, 1000),
        search=search,
        visitor_id=visitor_id,
    )

    unique_visitors = len({row.get("visitor_id") for row in rows if row.get("visitor_id")})
    unique_sessions = len({row.get("session_id") for row in rows if row.get("session_id")})
    unique_paths = len({row.get("path") for row in rows if row.get("path")})

    return jsonify(
        {
            "logs": rows,
            "summary": {
                "total": len(rows),
                "unique_visitors": unique_visitors,
                "unique_sessions": unique_sessions,
                "unique_paths": unique_paths,
            },
            "filters": {
                "q": search,
                "visitor_id": visitor_id,
                "limit": min(limit, 1000),
            },
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


@bp.route("/wbs/<int:task_id>")
def wbs_detail(task_id: int):
    task, selected_document_ids = get_repository_provider().wbs.fetch_task_with_links(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    document_options = _serialize_rows(
        get_repository_provider().common.fetch_document_link_options()
    )
    linked_documents = [
        document for document in document_options if document["id"] in set(selected_document_ids)
    ]

    return jsonify(
        {
            "task": dict(task),
            "linked_documents": linked_documents,
            "document_ids": list(selected_document_ids),
            "is_completed": _is_completed_task(task),
        }
    )


@bp.route("/wbs/editor")
def wbs_editor_bootstrap():
    task_id = parse_int(request.args.get("task_id"), default=0, minimum=0)
    task = None
    selected_document_ids = []
    if task_id:
        task, selected_document_ids = get_repository_provider().wbs.fetch_task_with_links(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404

    return jsonify(
        {
            "task": dict(task) if task else None,
            "selected_document_ids": list(selected_document_ids),
            "members": _serialize_rows(get_repository_provider().common.fetch_active_members()),
            "parent_tasks": _serialize_rows(
                get_repository_provider().common.fetch_parent_task_options(
                    exclude_task_id=task_id if task_id else None
                )
            ),
            "documents": _serialize_rows(get_repository_provider().common.fetch_document_link_options()),
            "statuses": list(TASK_STATUSES),
            "priorities": list(TASK_PRIORITIES),
            "platforms": list(WBS_PLATFORM_OPTIONS),
        }
    )


@bp.route("/wbs", methods=["POST"])
def create_wbs_task_api():
    data = _task_form_payload(request.get_json(silent=True) or {})
    errors = _validate_task_payload(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    task_id = get_repository_provider().wbs.create_task(data)
    get_repository_provider().wbs.sync_task_documents(task_id, data["document_ids"])
    db.commit()

    return jsonify({"task_id": task_id, "redirect_path": "/wbs"})


@bp.route("/wbs/<int:task_id>", methods=["POST"])
def update_wbs_task_api(task_id: int):
    existing_task, _selected_document_ids = get_repository_provider().wbs.fetch_task_with_links(task_id)
    if not existing_task:
        return jsonify({"error": "Task not found"}), 404

    data = _task_form_payload(request.get_json(silent=True) or {})
    errors = _validate_task_payload(data, task_id=task_id)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    get_repository_provider().wbs.update_task(task_id, data)
    get_repository_provider().wbs.sync_task_documents(task_id, data["document_ids"])
    db.commit()

    return jsonify({"task_id": task_id, "redirect_path": "/wbs"})


@bp.route("/wbs/<int:task_id>", methods=["DELETE"])
def delete_wbs_task_api(task_id: int):
    existing_task, _selected_document_ids = get_repository_provider().wbs.fetch_task_with_links(task_id)
    if not existing_task:
        return jsonify({"error": "Task not found"}), 404

    db = get_db()
    get_repository_provider().wbs.delete_task(task_id)
    db.commit()

    return jsonify({"deleted": True, "redirect_path": "/wbs"})


@bp.route("/members")
def members_list():
    members = get_repository_provider().members.list_members()
    return jsonify(
        {
            "members": _serialize_rows(members),
        }
    )


@bp.route("/members/editor")
def member_editor_bootstrap():
    member_id = parse_int(request.args.get("member_id"), default=0, minimum=0)
    member = None
    if member_id:
        member = get_repository_provider().members.fetch_member(member_id)
        if not member:
            return jsonify({"error": "Member not found"}), 404

    return jsonify(
        {
            "member": dict(member) if member else None,
        }
    )


@bp.route("/members", methods=["POST"])
def create_member_api():
    data = _member_form_payload(request.get_json(silent=True) or {})
    errors = _validate_member_payload(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    member_id = get_repository_provider().members.create_member(data)
    db.commit()

    return jsonify(
        {
            "member_id": member_id,
            "redirect_path": "/members",
        }
    )


@bp.route("/members/<int:member_id>", methods=["POST"])
def update_member_api(member_id: int):
    member = get_repository_provider().members.fetch_member(member_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404

    data = _member_form_payload(request.get_json(silent=True) or {})
    errors = _validate_member_payload(data)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    db = get_db()
    get_repository_provider().members.update_member(member_id, data)
    db.commit()

    return jsonify(
        {
            "member_id": member_id,
            "redirect_path": "/members",
        }
    )


@bp.route("/members/<int:member_id>", methods=["DELETE"])
def delete_member_api(member_id: int):
    member = get_repository_provider().members.fetch_member(member_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404

    db = get_db()
    get_repository_provider().members.delete_member(member_id)
    db.commit()

    return jsonify({"deleted": True, "redirect_path": "/members"})
