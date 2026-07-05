from __future__ import annotations


def fetch_task_with_links(db, task_id: int):
    task = db.execute(
        """
        SELECT t.*, m.name AS assignee_name, p.title AS parent_title
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        LEFT JOIN wbs_tasks p ON p.id = t.parent_id
        WHERE t.id = ?
        """,
        (task_id,),
    ).fetchone()
    if not task:
        return None, []

    document_ids = [
        row["document_id"]
        for row in db.execute(
            "SELECT document_id FROM task_documents WHERE task_id = ? ORDER BY document_id ASC",
            (task_id,),
        ).fetchall()
    ]
    return task, document_ids


def fetch_tasks_for_filters(db, filters: dict[str, str]):
    clauses = []
    params: list[str] = []

    if filters.get("status"):
        clauses.append("t.status = ?")
        params.append(filters["status"])
    if filters.get("assignee_id"):
        clauses.append("t.assignee_id = ?")
        params.append(filters["assignee_id"])
    if filters.get("priority"):
        clauses.append("t.priority = ?")
        params.append(filters["priority"])
    if filters.get("platform"):
        clauses.append("COALESCE(t.platform, 'Agentic Product Studio') = ?")
        params.append(filters["platform"])

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return db.execute(
        f"""
        SELECT
            t.*,
            m.name AS assignee_name,
            p.title AS parent_title
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        LEFT JOIN wbs_tasks p ON p.id = t.parent_id
        {where_sql}
        ORDER BY
            COALESCE(t.start_date, '9999-12-31') ASC,
            COALESCE(t.due_date, '9999-12-31') ASC,
            t.created_at ASC,
            t.id ASC
        """,
        params,
    ).fetchall()


def create_task(db, data):
    cursor = db.execute(
        """
        INSERT INTO wbs_tasks (
            parent_id, title, description, assignee_id, platform, status, priority,
            start_date, due_date, completed_date, progress, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["parent_id"],
            data["title"],
            data["description"],
            data["assignee_id"],
            data["platform"],
            data["status"],
            data["priority"],
            data["start_date"],
            data["due_date"],
            data["completed_date"],
            data["progress"],
            data["notes"],
        ),
    )
    return cursor.lastrowid


def update_task(db, task_id, data):
    db.execute(
        """
        UPDATE wbs_tasks
        SET parent_id = ?, title = ?, description = ?, assignee_id = ?, platform = ?,
            status = ?, priority = ?, start_date = ?, due_date = ?,
            completed_date = ?, progress = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            data["parent_id"],
            data["title"],
            data["description"],
            data["assignee_id"],
            data["platform"],
            data["status"],
            data["priority"],
            data["start_date"],
            data["due_date"],
            data["completed_date"],
            data["progress"],
            data["notes"],
            task_id,
        ),
    )


def delete_task(db, task_id):
    db.execute("DELETE FROM task_documents WHERE task_id = ?", (task_id,))
    db.execute(
        "UPDATE schedules SET wbs_task_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE wbs_task_id = ?",
        (task_id,),
    )
    db.execute("UPDATE wbs_tasks SET parent_id = NULL WHERE parent_id = ?", (task_id,))
    db.execute("DELETE FROM wbs_tasks WHERE id = ?", (task_id,))
