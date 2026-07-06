from __future__ import annotations


def fetch_member(db, member_id: int):
    return db.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()


def list_members(db):
    return db.execute(
        """
        SELECT
            m.*,
            COALESCE(task_counts.task_count, 0) AS task_count,
            COALESCE(schedule_counts.schedule_count, 0) AS schedule_count
        FROM members m
        LEFT JOIN (
            SELECT assignee_id, COUNT(*) AS task_count
            FROM wbs_tasks
            WHERE assignee_id IS NOT NULL
            GROUP BY assignee_id
        ) task_counts ON task_counts.assignee_id = m.id
        LEFT JOIN (
            SELECT assignee_id, COUNT(*) AS schedule_count
            FROM schedules
            WHERE assignee_id IS NOT NULL
            GROUP BY assignee_id
        ) schedule_counts ON schedule_counts.assignee_id = m.id
        ORDER BY m.is_active DESC, m.name COLLATE NOCASE ASC
        """
    ).fetchall()


def create_member(db, data):
    db.execute(
        """
        INSERT INTO members (name, role, part, contact, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        (data["name"], data["role"], data["part"], data["contact"], data["is_active"]),
    )


def update_member(db, member_id: int, data):
    db.execute(
        """
        UPDATE members
        SET name = ?, role = ?, part = ?, contact = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (data["name"], data["role"], data["part"], data["contact"], data["is_active"], member_id),
    )


def delete_member(db, member_id: int):
    db.execute(
        "UPDATE wbs_tasks SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
        (member_id,),
    )
    db.execute(
        "UPDATE schedules SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
        (member_id,),
    )
    db.execute(
        "UPDATE documents SET author_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE author_id = ?",
        (member_id,),
    )
    db.execute("DELETE FROM members WHERE id = ?", (member_id,))
