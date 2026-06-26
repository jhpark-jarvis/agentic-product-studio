from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .constants import SCHEDULE_TYPES
from .db import get_db
from .utils import month_bounds, parse_date, today_local, week_bounds


bp = Blueprint("schedules", __name__, url_prefix="/schedules")


def _fetch_members():
    return get_db().execute(
        "SELECT id, name FROM members WHERE is_active = 1 ORDER BY name COLLATE NOCASE ASC"
    ).fetchall()


def _fetch_tasks():
    return get_db().execute(
        "SELECT id, title FROM wbs_tasks ORDER BY updated_at DESC, id DESC"
    ).fetchall()


def _schedule_form_data():
    return {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "start_date": request.form.get("start_date") or None,
        "end_date": request.form.get("end_date") or None,
        "assignee_id": request.form.get("assignee_id") or None,
        "wbs_task_id": request.form.get("wbs_task_id") or None,
        "schedule_type": request.form.get("schedule_type", SCHEDULE_TYPES[0]),
    }


def _validate_schedule_form(data):
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
    return errors


def _fetch_schedule(schedule_id: int):
    return get_db().execute(
        """
        SELECT s.*, m.name AS assignee_name, t.title AS task_title
        FROM schedules s
        LEFT JOIN members m ON m.id = s.assignee_id
        LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
        WHERE s.id = ?
        """,
        (schedule_id,),
    ).fetchone()


def _build_month_days(schedules, month_start, month_end, today):
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
            starts_today = cursor == start
            ends_today = cursor == end
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
                    "starts_today": starts_today,
                    "ends_today": ends_today,
                    "is_multi_day": start != end,
                }
            )
            cursor += timedelta(days=1)

    ordered_days = []
    cursor = month_start
    while cursor <= month_end:
        day_items = per_day.get(cursor.isoformat(), [])
        start_items = [item for item in day_items if item["starts_today"]][:2]
        continuing_count = sum(1 for item in day_items if not item["starts_today"])
        hidden_start_count = max(0, len([item for item in day_items if item["starts_today"]]) - len(start_items))
        ordered_days.append(
            {
                "date": cursor,
                "is_today": cursor.isoformat() == today.isoformat(),
                "item_count": len(day_items),
                "start_items": start_items,
                "continuing_count": continuing_count,
                "hidden_start_count": hidden_start_count,
                "modal_items": day_items,
            }
        )
        cursor += timedelta(days=1)
    return ordered_days


@bp.route("/")
def list_schedules():
    db = get_db()
    today = today_local()
    week_start, week_end = week_bounds(today)

    month_query = request.args.get("month", today.strftime("%Y-%m"))
    try:
        month_reference = datetime.strptime(month_query + "-01", "%Y-%m-%d").date()
    except ValueError:
        month_reference = today.replace(day=1)
        month_query = month_reference.strftime("%Y-%m")

    month_start, month_end = month_bounds(month_reference)
    schedules = db.execute(
        """
        SELECT s.*, m.name AS assignee_name, t.title AS task_title
        FROM schedules s
        LEFT JOIN members m ON m.id = s.assignee_id
        LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
        ORDER BY s.start_date ASC, s.end_date ASC, s.id ASC
        """
    ).fetchall()

    week_items = []
    for item in schedules:
        start = parse_date(item["start_date"])
        end = parse_date(item["end_date"]) or start
        if not start:
            continue
        if end >= week_start and start <= week_end:
            week_items.append(item)

    return render_template(
        "schedules/list_v2.html",
        schedules=schedules,
        week_items=week_items,
        month_days=_build_month_days(schedules, month_start, month_end, today),
        today=today,
        week_start=week_start,
        week_end=week_end,
        month_query=month_query,
    )


@bp.route("/new", methods=("GET", "POST"))
def create_schedule():
    db = get_db()
    if request.method == "POST":
        data = _schedule_form_data()
        errors = _validate_schedule_form(data)
        if not errors:
            db.execute(
                """
                INSERT INTO schedules (title, description, start_date, end_date, assignee_id, wbs_task_id, schedule_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["title"],
                    data["description"],
                    data["start_date"],
                    data["end_date"],
                    data["assignee_id"],
                    data["wbs_task_id"],
                    data["schedule_type"],
                ),
            )
            db.commit()
            flash("일정이 생성되었습니다.", "success")
            return redirect(url_for("schedules.list_schedules"))
        for error in errors:
            flash(error, "error")
        form_data = data
    else:
        form_data = None

    return render_template(
        "schedules/form.html",
        page_title="새 일정",
        submit_label="일정 저장",
        schedule=None,
        schedule_types=SCHEDULE_TYPES,
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
    )


@bp.route("/<int:schedule_id>/edit", methods=("GET", "POST"))
def edit_schedule(schedule_id: int):
    db = get_db()
    schedule = _fetch_schedule(schedule_id)
    if not schedule:
        flash("일정을 찾을 수 없습니다.", "error")
        return redirect(url_for("schedules.list_schedules"))

    if request.method == "POST":
        data = _schedule_form_data()
        errors = _validate_schedule_form(data)
        if not errors:
            db.execute(
                """
                UPDATE schedules
                SET title = ?, description = ?, start_date = ?, end_date = ?,
                    assignee_id = ?, wbs_task_id = ?, schedule_type = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    data["title"],
                    data["description"],
                    data["start_date"],
                    data["end_date"],
                    data["assignee_id"],
                    data["wbs_task_id"],
                    data["schedule_type"],
                    schedule_id,
                ),
            )
            db.commit()
            flash("일정이 수정되었습니다.", "success")
            return redirect(url_for("schedules.list_schedules"))
        for error in errors:
            flash(error, "error")
        form_data = data
    else:
        form_data = None

    return render_template(
        "schedules/form.html",
        page_title="일정 수정",
        submit_label="변경 저장",
        schedule=schedule,
        schedule_types=SCHEDULE_TYPES,
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
    )


@bp.route("/<int:schedule_id>/delete", methods=("POST",))
def delete_schedule(schedule_id: int):
    db = get_db()
    db.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    db.commit()
    flash("일정이 삭제되었습니다.", "success")
    return redirect(url_for("schedules.list_schedules"))
