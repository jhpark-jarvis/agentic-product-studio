from __future__ import annotations


def fetch_member(db, member_id: int):
    return db.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()


def list_members(db):
    return db.execute(
        """
        SELECT
            m.*,
            (SELECT COUNT(*) FROM wbs_tasks t WHERE t.assignee_id = m.id) AS task_count,
            (SELECT COUNT(*) FROM schedules s WHERE s.assignee_id = m.id) AS schedule_count
        FROM members m
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
