from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .constants import TASK_PRIORITIES, TASK_STATUSES
from .db import get_db
from .repositories.provider import get_repository_provider
from .utils import WBS_PLATFORM_OPTIONS, parse_date, today_local


bp = Blueprint("wbs", __name__, url_prefix="/wbs")


def _fetch_members():
    return get_repository_provider().common.fetch_active_members()


def _fetch_documents():
    return get_repository_provider().common.fetch_document_link_options()


def _fetch_task_with_links(task_id: int):
    return get_repository_provider().wbs.fetch_task_with_links(task_id)


def _is_completed_task(task) -> bool:
    completed_status = TASK_STATUSES[3] if len(TASK_STATUSES) > 3 else "완료"
    status = (task["status"] or "").strip()
    completed_date = parse_date(task["completed_date"])
    progress = task["progress"] or 0
    return status == completed_status or completed_date is not None or progress >= 100


def _fetch_flattened_tasks(filters: dict[str, str]):
    tasks = get_repository_provider().wbs.fetch_tasks_for_filters(filters)

    children: dict[int | None, list] = defaultdict(list)
    by_id = {task["id"]: task for task in tasks}
    for task in tasks:
        parent_id = task["parent_id"] if task["parent_id"] in by_id else None
        children[parent_id].append(task)

    today = today_local()
    flattened = []

    def walk(parent_id: int | None, depth: int):
        for task in children.get(parent_id, []):
            due = parse_date(task["due_date"])
            completed = _is_completed_task(task)
            is_delayed = bool(due and due < today and not completed)
            is_due_soon = bool(due and 0 <= (due - today).days <= 3 and not completed)
            flattened.append(
                {
                    "task": task,
                    "depth": depth,
                    "is_delayed": is_delayed,
                    "is_due_soon": is_due_soon,
                }
            )
            walk(task["id"], depth + 1)

    walk(None, 0)
    return flattened


def _task_form_data():
    selected_docs = request.form.getlist("document_ids")
    return {
        "parent_id": request.form.get("parent_id") or None,
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "assignee_id": request.form.get("assignee_id") or None,
        "platform": request.form.get("platform", WBS_PLATFORM_OPTIONS[0]).strip(),
        "status": request.form.get("status", "예정"),
        "priority": request.form.get("priority", "보통"),
        "start_date": request.form.get("start_date") or None,
        "due_date": request.form.get("due_date") or None,
        "completed_date": request.form.get("completed_date") or None,
        "progress": request.form.get("progress", "0").strip() or "0",
        "notes": request.form.get("notes", "").strip(),
        "document_ids": [int(value) for value in selected_docs if value.isdigit()],
    }


def _validate_task_form(data, task_id: int | None = None):
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


@bp.route("/")
def list_tasks():
    filters = {
        "status": request.args.get("status", ""),
        "assignee_id": request.args.get("assignee_id", ""),
        "priority": request.args.get("priority", ""),
        "platform": request.args.get("platform", ""),
    }
    return render_template(
        "wbs/list.html",
        task_rows=_fetch_flattened_tasks(filters),
        members=_fetch_members(),
        statuses=TASK_STATUSES,
        priorities=TASK_PRIORITIES,
        platforms=WBS_PLATFORM_OPTIONS,
        filters=filters,
    )


@bp.route("/new", methods=("GET", "POST"))
def create_task():
    db = get_db()
    if request.method == "POST":
        data = _task_form_data()
        errors = _validate_task_form(data)
        if not errors:
            task_id = get_repository_provider().wbs.create_task(data)
            get_repository_provider().wbs.sync_task_documents(task_id, data["document_ids"])
            db.commit()
            flash("WBS 작업이 생성되었습니다.", "success")
            return redirect(url_for("wbs.list_tasks"))
        for error in errors:
            flash(error, "error")
        form_data = data
    else:
        form_data = None

    return render_template(
        "wbs/form.html",
        page_title="새 WBS 작업",
        submit_label="작업 생성",
        task=None,
        selected_document_ids=[] if form_data is None else form_data["document_ids"],
        members=_fetch_members(),
        parent_tasks=get_repository_provider().common.fetch_parent_task_options(),
        documents=_fetch_documents(),
        statuses=TASK_STATUSES,
        priorities=TASK_PRIORITIES,
        platforms=WBS_PLATFORM_OPTIONS,
        form_data=form_data,
    )


@bp.route("/<int:task_id>/edit", methods=("GET", "POST"))
def edit_task(task_id: int):
    db = get_db()
    task, selected_document_ids = _fetch_task_with_links(task_id)
    if not task:
        flash("작업을 찾을 수 없습니다.", "error")
        return redirect(url_for("wbs.list_tasks"))

    if request.method == "POST":
        data = _task_form_data()
        errors = _validate_task_form(data, task_id=task_id)
        if not errors:
            get_repository_provider().wbs.update_task(task_id, data)
            get_repository_provider().wbs.sync_task_documents(task_id, data["document_ids"])
            db.commit()
            flash("WBS 작업이 수정되었습니다.", "success")
            return redirect(url_for("wbs.list_tasks"))
        for error in errors:
            flash(error, "error")
        form_data = data
        selected_document_ids = data["document_ids"]
    else:
        form_data = None

    return render_template(
        "wbs/form.html",
        page_title="WBS 작업 수정",
        submit_label="변경 저장",
        task=task,
        selected_document_ids=selected_document_ids,
        members=_fetch_members(),
        parent_tasks=get_repository_provider().common.fetch_parent_task_options(
            exclude_task_id=task_id
        ),
        documents=_fetch_documents(),
        statuses=TASK_STATUSES,
        priorities=TASK_PRIORITIES,
        platforms=WBS_PLATFORM_OPTIONS,
        form_data=form_data,
    )


@bp.route("/<int:task_id>/delete", methods=("POST",))
def delete_task(task_id: int):
    db = get_db()
    get_repository_provider().wbs.delete_task(task_id)
    db.commit()
    flash("WBS 작업이 삭제되었습니다.", "success")
    return redirect(url_for("wbs.list_tasks"))
