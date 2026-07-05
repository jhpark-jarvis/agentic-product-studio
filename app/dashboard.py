from flask import Blueprint, render_template

from .db import get_db
from .repositories.dashboard import (
    fetch_dashboard_summary,
    fetch_pinned_notice,
    fetch_recent_documents,
    fetch_recent_tasks,
    fetch_upcoming_schedules,
    fetch_week_due_tasks,
)
from .utils import today_local, week_bounds


bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    db = get_db()
    today = today_local()
    _, week_end = week_bounds(today)
    today_str = today.isoformat()
    week_end_str = week_end.isoformat()

    summary = fetch_dashboard_summary(db, today_str)
    week_due_tasks = fetch_week_due_tasks(db, today_str, week_end_str)
    recent_documents = fetch_recent_documents(db)
    recent_tasks = fetch_recent_tasks(db)
    pinned_notice = fetch_pinned_notice(db)
    upcoming_schedules = fetch_upcoming_schedules(db, today_str)

    return render_template(
        "dashboard/index.html",
        summary=summary,
        week_due_tasks=week_due_tasks,
        week_due_task_count=len(week_due_tasks),
        recent_documents=recent_documents,
        recent_document_count=len(recent_documents),
        recent_tasks=recent_tasks,
        recent_task_count=len(recent_tasks),
        pinned_notice=pinned_notice,
        upcoming_schedules=upcoming_schedules,
        upcoming_schedule_count=len(upcoming_schedules),
        today=today,
        week_end=week_end,
    )
