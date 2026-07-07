from __future__ import annotations


def fetch_schedule(db, schedule_id: int):
    return db.execute(
        """
        SELECT s.*, m.name AS assignee_name, t.title AS task_title
        FROM schedules s
        LEFT JOIN members m ON m.id = s.assignee_id
        LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
        WHERE s.id = ?
        """,
        (schedule_id,),
    ).fetchone()


def list_schedules(db):
    return db.execute(
        """
        SELECT s.*, m.name AS assignee_name, t.title AS task_title
        FROM schedules s
        LEFT JOIN members m ON m.id = s.assignee_id
        LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
        ORDER BY s.start_date ASC, s.end_date ASC, s.id ASC
        """
    ).fetchall()


def create_schedule(db, data):
    cursor = db.execute(
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
    return cursor.lastrowid


def update_schedule(db, schedule_id: int, data):
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


def delete_schedule(db, schedule_id: int):
    db.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
