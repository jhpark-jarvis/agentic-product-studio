from __future__ import annotations


def fetch_dashboard_summary(db, today_str: str):
    return db.execute(
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


def fetch_week_due_tasks(db, today_str: str, week_end_str: str):
    return db.execute(
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


def fetch_recent_documents(db):
    return db.execute(
        """
        SELECT d.id, d.title, d.doc_type, d.updated_at, m.name AS author_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
        WHERE COALESCE(d.is_hidden, 0) = 0
        ORDER BY d.updated_at DESC, d.id DESC
        LIMIT 6
        """
    ).fetchall()


def fetch_recent_tasks(db):
    return db.execute(
        """
        SELECT t.id, t.title, t.status, t.priority, t.updated_at, m.name AS assignee_name
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        ORDER BY t.updated_at DESC, t.id DESC
        LIMIT 6
        """
    ).fetchall()


def fetch_pinned_notice(db):
    return db.execute(
        """
        SELECT id, title, content, updated_at
        FROM notices
        WHERE is_pinned = 1
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()


def fetch_upcoming_schedules(db, today_str: str):
    return db.execute(
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
