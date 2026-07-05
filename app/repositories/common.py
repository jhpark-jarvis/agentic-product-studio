from __future__ import annotations


def fetch_active_members(db):
    return db.execute(
        """
        SELECT id, name, role, part
        FROM members
        WHERE is_active = 1
        ORDER BY name COLLATE NOCASE ASC
        """
    ).fetchall()


def fetch_document_link_options(db):
    return db.execute(
        """
        SELECT id, title, doc_type, is_hidden
        FROM documents
        ORDER BY is_hidden ASC, updated_at DESC, title COLLATE NOCASE ASC
        """
    ).fetchall()


def fetch_task_link_options(db):
    return db.execute(
        """
        SELECT id, title, status
        FROM wbs_tasks
        ORDER BY updated_at DESC, id DESC
        """
    ).fetchall()


def fetch_parent_task_options(db, exclude_task_id: int | None = None):
    if exclude_task_id is None:
        return db.execute(
            "SELECT id, title FROM wbs_tasks ORDER BY created_at ASC, id ASC"
        ).fetchall()

    return db.execute(
        """
        SELECT id, title
        FROM wbs_tasks
        WHERE id != ?
        ORDER BY created_at ASC, id ASC
        """,
        (exclude_task_id,),
    ).fetchall()
