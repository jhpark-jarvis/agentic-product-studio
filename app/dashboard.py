from flask import Blueprint, render_template

from .db import get_db
from .utils import today_local, week_bounds


bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    db = get_db()
    today = today_local()
    _, week_end = week_bounds(today)
    today_str = today.isoformat()
    week_end_str = week_end.isoformat()

    summary = db.execute(
        """
        SELECT
            COUNT(*) AS total_tasks,
            SUM(CASE WHEN status IN ('진행중', '검토중') THEN 1 ELSE 0 END) AS in_progress_tasks,
            SUM(CASE WHEN status = '완료' THEN 1 ELSE 0 END) AS completed_tasks,
            SUM(
                CASE
                    WHEN due_date IS NOT NULL
                     AND due_date < ?
                     AND status != '완료'
                    THEN 1 ELSE 0
                END
            ) AS delayed_tasks
        FROM wbs_tasks
        """,
        (today_str,),
    ).fetchone()

    week_due_tasks = db.execute(
        """
        SELECT t.id, t.title, t.status, t.priority, t.due_date, m.name AS assignee_name
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        WHERE t.due_date BETWEEN ? AND ?
          AND t.status != '완료'
        ORDER BY t.due_date ASC, t.id ASC
        LIMIT 8
        """,
        (today_str, week_end_str),
    ).fetchall()

    recent_documents = db.execute(
        """
        SELECT d.id, d.title, d.doc_type, d.updated_at, m.name AS author_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
        WHERE COALESCE(d.is_hidden, 0) = 0
        ORDER BY d.updated_at DESC, d.id DESC
        LIMIT 6
        """
    ).fetchall()

    recent_tasks = db.execute(
        """
        SELECT t.id, t.title, t.status, t.priority, t.updated_at, m.name AS assignee_name
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        ORDER BY t.updated_at DESC, t.id DESC
        LIMIT 6
        """
    ).fetchall()

    pinned_notice = db.execute(
        """
        SELECT id, title, content, updated_at
        FROM notices
        WHERE is_pinned = 1
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()

    upcoming_schedules = db.execute(
        """
        SELECT
            s.id,
            s.title,
            s.start_date,
            s.end_date,
            s.schedule_type,
            m.name AS assignee_name,
            t.title AS task_title
        FROM schedules s
        LEFT JOIN members m ON m.id = s.assignee_id
        LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
        WHERE s.end_date >= ?
        ORDER BY s.start_date ASC, s.id ASC
        LIMIT 6
        """,
        (today_str,),
    ).fetchall()

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
