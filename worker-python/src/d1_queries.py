from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def _to_jsonable_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return result.get("results", []) if isinstance(result, dict) else []


async def execute(env, sql: str, *params):
    return await env.DB.prepare(sql).bind(*params).run()


async def query_all(env, sql: str, *params):
    result = await execute(env, sql, *params)
    return _to_jsonable_rows(result)


async def query_first(env, sql: str, *params):
    rows = await query_all(env, sql, *params)
    return rows[0] if rows else None


def week_bounds(today: date):
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


def normalize_tags(tags_text: str) -> list[str]:
    tags: list[str] = []
    for raw in (tags_text or "").split(","):
        tag = raw.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


async def fetch_dashboard_payload(env):
    today = date.today()
    _, week_end = week_bounds(today)
    today_str = today.isoformat()
    week_end_str = week_end.isoformat()

    summary = await query_first(
        env,
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
        today_str,
    )

    week_due_tasks = await query_all(
        env,
        """
        SELECT t.id, t.title, t.status, t.priority, t.due_date, m.name AS assignee_name
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        WHERE t.due_date BETWEEN ? AND ?
          AND t.status != '완료'
        ORDER BY t.due_date ASC, t.id ASC
        LIMIT 8
        """,
        today_str,
        week_end_str,
    )

    recent_documents = await query_all(
        env,
        """
        SELECT d.id, d.title, d.doc_type, d.updated_at, m.name AS author_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
        WHERE COALESCE(d.is_hidden, 0) = 0
        ORDER BY d.updated_at DESC, d.id DESC
        LIMIT 6
        """,
    )

    recent_tasks = await query_all(
        env,
        """
        SELECT t.id, t.title, t.status, t.priority, t.updated_at, m.name AS assignee_name
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        ORDER BY t.updated_at DESC, t.id DESC
        LIMIT 6
        """,
    )

    pinned_notice = await query_first(
        env,
        """
        SELECT id, title, content, updated_at
        FROM notices
        WHERE is_pinned = 1
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
    )

    upcoming_schedules = await query_all(
        env,
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
        today_str,
    )

    return {
        "today": today_str,
        "week_end": week_end_str,
        "summary": summary or {},
        "week_due_tasks": week_due_tasks,
        "recent_documents": recent_documents,
        "recent_tasks": recent_tasks,
        "pinned_notice": pinned_notice,
        "upcoming_schedules": upcoming_schedules,
    }


async def fetch_documents_payload(
    env,
    *,
    search: str,
    doc_type: str,
    tag: str,
    folder_id: str,
    limit: int,
    offset: int,
):
    clauses = ["d.is_hidden = 0"]
    params: list[Any] = []
    joins = [
        "LEFT JOIN members m ON m.id = d.author_id",
        "LEFT JOIN document_folders f ON f.id = d.folder_id",
    ]

    if search:
        clauses.append("(d.title LIKE ? OR d.content LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if doc_type:
        clauses.append("d.doc_type = ?")
        params.append(doc_type)
    if tag:
        joins.append("JOIN document_tags dt_filter ON dt_filter.document_id = d.id")
        clauses.append("dt_filter.tag = ?")
        params.append(tag)
    if folder_id.isdigit():
        clauses.append("d.folder_id = ?")
        params.append(int(folder_id))

    where_sql = f"WHERE {' AND '.join(clauses)}"

    total_count_row = await query_first(
        env,
        f"""
        SELECT COUNT(DISTINCT d.id) AS count
        FROM documents d
        {' '.join(joins)}
        {where_sql}
        """,
        *params,
    )

    documents = await query_all(
        env,
        f"""
        SELECT DISTINCT
            d.id,
            d.title,
            d.doc_type,
            d.updated_at,
            d.is_hidden,
            m.name AS author_name,
            f.id AS folder_id,
            f.name AS folder_name
        FROM documents d
        {' '.join(joins)}
        {where_sql}
        ORDER BY d.updated_at DESC, d.id DESC
        LIMIT ? OFFSET ?
        """,
        *params,
        limit,
        offset,
    )

    tag_options = await query_all(
        env,
        """
        SELECT tag, COUNT(*) AS usage_count
        FROM document_tags
        GROUP BY tag
        ORDER BY tag COLLATE NOCASE ASC
        """,
    )

    folder_options = await query_all(
        env,
        """
        SELECT id, doc_type, name
        FROM document_folders
        ORDER BY doc_type COLLATE NOCASE ASC, name COLLATE NOCASE ASC
        """,
    )

    return {
        "total_count": (total_count_row or {}).get("count", 0),
        "documents": documents,
        "tag_options": tag_options,
        "folder_options": folder_options,
        "filters": {
            "q": search,
            "doc_type": doc_type,
            "tag": tag,
            "folder_id": folder_id,
        },
        "limit": limit,
        "offset": offset,
    }


async def fetch_document_detail_payload(env, document_id: int):
    document = await query_first(
        env,
        """
        SELECT d.*, m.name AS author_name, f.name AS folder_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
        LEFT JOIN document_folders f ON f.id = d.folder_id
        WHERE d.id = ?
        """,
        document_id,
    )
    if not document:
        return None

    related_tasks = await query_all(
        env,
        """
        SELECT t.id, t.title, t.status, t.priority
        FROM task_documents td
        JOIN wbs_tasks t ON t.id = td.task_id
        WHERE td.document_id = ?
        ORDER BY t.updated_at DESC, t.id DESC
        """,
        document_id,
    )
    tags = await query_all(
        env,
        """
        SELECT tag
        FROM document_tags
        WHERE document_id = ?
        ORDER BY tag COLLATE NOCASE ASC
        """,
        document_id,
    )
    assets = await query_all(
        env,
        """
        SELECT id, document_id, object_key, url, original_filename, content_type, size, created_at
        FROM document_assets
        WHERE document_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        document_id,
    )

    return {
        "document": document,
        "related_tasks": related_tasks,
        "tags": [row["tag"] for row in tags],
        "assets": assets,
    }


async def fetch_document_assets_payload(env, document_id: int):
    assets = await query_all(
        env,
        """
        SELECT id, document_id, draft_key, object_key, url, original_filename, content_type, size, created_at
        FROM document_assets
        WHERE document_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        document_id,
    )
    return {"assets": assets}


async def fetch_document_asset_payload(env, asset_id: int):
    return await query_first(
        env,
        """
        SELECT id, document_id, draft_key, object_key, url, original_filename, content_type, size, created_at
        FROM document_assets
        WHERE id = ?
        """,
        asset_id,
    )


async def create_document_asset_record(
    env,
    *,
    document_id: int | None,
    draft_key: str | None,
    object_key: str,
    url: str,
    original_filename: str,
    content_type: str,
    size: int,
):
    result = await execute(
        env,
        """
        INSERT INTO document_assets (
            document_id, draft_key, object_key, url, original_filename, content_type, size, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        document_id,
        draft_key,
        object_key,
        url,
        original_filename,
        content_type,
        size,
    )
    meta = result.get("meta", {}) if isinstance(result, dict) else {}
    return meta.get("last_row_id")


async def assign_draft_assets_to_document_record(env, document_id: int, draft_key: str):
    if not draft_key:
        return
    await execute(
        env,
        """
        UPDATE document_assets
        SET document_id = ?, draft_key = NULL
        WHERE draft_key = ? AND document_id IS NULL
        """,
        document_id,
        draft_key,
    )


async def fetch_wbs_payload(env, *, status: str, assignee_id: str, priority: str, platform: str):
    clauses = []
    params: list[Any] = []

    if status:
        clauses.append("t.status = ?")
        params.append(status)
    if assignee_id.isdigit():
        clauses.append("t.assignee_id = ?")
        params.append(int(assignee_id))
    if priority:
        clauses.append("t.priority = ?")
        params.append(priority)
    if platform:
        clauses.append("COALESCE(t.platform, 'Agentic Product Studio') = ?")
        params.append(platform)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    tasks = await query_all(
        env,
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
        *params,
    )

    return {
        "tasks": tasks,
        "filters": {
            "status": status,
            "assignee_id": assignee_id,
            "priority": priority,
            "platform": platform,
        },
    }


async def fetch_wbs_detail_payload(env, task_id: int):
    task = await query_first(
        env,
        """
        SELECT
            t.*,
            m.name AS assignee_name,
            p.title AS parent_title
        FROM wbs_tasks t
        LEFT JOIN members m ON m.id = t.assignee_id
        LEFT JOIN wbs_tasks p ON p.id = t.parent_id
        WHERE t.id = ?
        """,
        task_id,
    )
    if not task:
        return None

    linked_documents = await query_all(
        env,
        """
        SELECT d.id, d.title, d.doc_type, d.updated_at
        FROM task_documents td
        JOIN documents d ON d.id = td.document_id
        WHERE td.task_id = ?
        ORDER BY d.updated_at DESC, d.id DESC
        """,
        task_id,
    )

    return {
        "task": task,
        "linked_documents": linked_documents,
        "document_ids": [item["id"] for item in linked_documents],
    }


async def fetch_members_payload(env):
    members = await query_all(
        env,
        """
        SELECT
            m.*,
            (SELECT COUNT(*) FROM wbs_tasks t WHERE t.assignee_id = m.id) AS task_count,
            (SELECT COUNT(*) FROM schedules s WHERE s.assignee_id = m.id) AS schedule_count
        FROM members m
        ORDER BY m.is_active DESC, m.name COLLATE NOCASE ASC
        """,
    )
    return {"members": members}


async def fetch_member_detail_payload(env, member_id: int):
    member = await query_first(
        env,
        """
        SELECT
            m.*,
            (SELECT COUNT(*) FROM wbs_tasks t WHERE t.assignee_id = m.id) AS task_count,
            (SELECT COUNT(*) FROM schedules s WHERE s.assignee_id = m.id) AS schedule_count
        FROM members m
        WHERE m.id = ?
        """,
        member_id,
    )
    if not member:
        return None

    assigned_tasks = await query_all(
        env,
        """
        SELECT id, title, status, priority, due_date, progress, updated_at
        FROM wbs_tasks
        WHERE assignee_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 20
        """,
        member_id,
    )

    schedules = await query_all(
        env,
        """
        SELECT id, title, start_date, end_date, schedule_type, wbs_task_id, updated_at
        FROM schedules
        WHERE assignee_id = ?
        ORDER BY start_date ASC, end_date ASC, id ASC
        LIMIT 20
        """,
        member_id,
    )

    authored_documents = await query_all(
        env,
        """
        SELECT id, title, doc_type, updated_at
        FROM documents
        WHERE author_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 20
        """,
        member_id,
    )

    return {
        "member": member,
        "assigned_tasks": assigned_tasks,
        "schedules": schedules,
        "authored_documents": authored_documents,
    }


async def fetch_schedules_payload(env):
    schedules = await query_all(
        env,
        """
        SELECT s.*, m.name AS assignee_name, t.title AS task_title
        FROM schedules s
        LEFT JOIN members m ON m.id = s.assignee_id
        LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
        ORDER BY s.start_date ASC, s.end_date ASC, s.id ASC
        """,
    )
    return {"schedules": schedules}


async def fetch_schedule_detail_payload(env, schedule_id: int):
    return await query_first(
        env,
        """
        SELECT s.*, m.name AS assignee_name, t.title AS task_title
        FROM schedules s
        LEFT JOIN members m ON m.id = s.assignee_id
        LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
        WHERE s.id = ?
        """,
        schedule_id,
    )


async def fetch_common_options_payload(env, *, exclude_task_id: int | None = None):
    active_members = await query_all(
        env,
        """
        SELECT id, name, role, part
        FROM members
        WHERE is_active = 1
        ORDER BY name COLLATE NOCASE ASC
        """,
    )

    document_link_options = await query_all(
        env,
        """
        SELECT id, title, doc_type, is_hidden
        FROM documents
        ORDER BY is_hidden ASC, updated_at DESC, title COLLATE NOCASE ASC
        """,
    )

    task_link_options = await query_all(
        env,
        """
        SELECT id, title, status
        FROM wbs_tasks
        ORDER BY updated_at DESC, id DESC
        """,
    )

    if exclude_task_id is None:
        parent_task_options = await query_all(
            env,
            """
            SELECT id, title
            FROM wbs_tasks
            ORDER BY created_at ASC, id ASC
            """,
        )
    else:
        parent_task_options = await query_all(
            env,
            """
            SELECT id, title
            FROM wbs_tasks
            WHERE id != ?
            ORDER BY created_at ASC, id ASC
            """,
            exclude_task_id,
        )

    return {
        "active_members": active_members,
        "document_link_options": document_link_options,
        "task_link_options": task_link_options,
        "parent_task_options": parent_task_options,
    }


async def fetch_document_folders_payload(env, doc_type: str | None = None):
    if doc_type:
        folders = await query_all(
            env,
            """
            SELECT id, doc_type, name
            FROM document_folders
            WHERE doc_type = ?
            ORDER BY name COLLATE NOCASE ASC
            """,
            doc_type,
        )
    else:
        folders = await query_all(
            env,
            """
            SELECT id, doc_type, name
            FROM document_folders
            ORDER BY doc_type COLLATE NOCASE ASC, name COLLATE NOCASE ASC
            """,
        )
    return {"folders": folders}


async def create_document_folder_record(env, *, doc_type: str, folder_name: str):
    existing = await query_first(
        env,
        """
        SELECT id, doc_type, name
        FROM document_folders
        WHERE doc_type = ? AND lower(name) = lower(?)
        """,
        doc_type,
        folder_name.strip(),
    )
    if existing:
        return existing["id"]

    result = await execute(
        env,
        """
        INSERT INTO document_folders (doc_type, name, created_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
        doc_type,
        folder_name.strip(),
    )
    return result.get("meta", {}).get("last_row_id")


async def sync_document_tags(env, document_id: int, tags_text: str):
    await execute(env, "DELETE FROM document_tags WHERE document_id = ?", document_id)
    for tag in normalize_tags(tags_text):
        await execute(
            env,
            "INSERT INTO document_tags (document_id, tag) VALUES (?, ?)",
            document_id,
            tag,
        )


async def sync_document_task_links(env, document_id: int, task_ids: list[int]):
    await execute(env, "DELETE FROM task_documents WHERE document_id = ?", document_id)
    for task_id in sorted(set(task_ids)):
        await execute(
            env,
            "INSERT OR IGNORE INTO task_documents (task_id, document_id) VALUES (?, ?)",
            task_id,
            document_id,
        )


async def create_document_record(
    env,
    *,
    title: str,
    doc_type: str,
    folder_id: int | None,
    is_hidden: int,
    content: str,
    author_id: int | None,
    tags: str,
):
    result = await execute(
        env,
        """
        INSERT INTO documents (
            title, doc_type, folder_id, is_hidden, content, author_id, tags, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        title,
        doc_type,
        folder_id,
        is_hidden,
        content,
        author_id,
        tags,
    )
    return result.get("meta", {}).get("last_row_id")


async def update_document_record(
    env,
    document_id: int,
    *,
    title: str,
    doc_type: str,
    folder_id: int | None,
    is_hidden: int,
    content: str,
    author_id: int | None,
    tags: str,
):
    await execute(
        env,
        """
        UPDATE documents
        SET title = ?, doc_type = ?, folder_id = ?, is_hidden = ?,
            content = ?, author_id = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        title,
        doc_type,
        folder_id,
        is_hidden,
        content,
        author_id,
        tags,
        document_id,
    )


async def update_document_folder_record(
    env,
    document_id: int,
    *,
    doc_type: str,
    folder_id: int | None,
):
    await execute(
        env,
        """
        UPDATE documents
        SET doc_type = ?, folder_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        doc_type,
        folder_id,
        document_id,
    )


async def delete_document_record(env, document_id: int):
    await execute(env, "DELETE FROM document_assets WHERE document_id = ?", document_id)
    await execute(env, "DELETE FROM task_documents WHERE document_id = ?", document_id)
    await execute(env, "DELETE FROM document_tags WHERE document_id = ?", document_id)
    await execute(env, "DELETE FROM documents WHERE id = ?", document_id)


async def delete_document_asset_record(env, asset_id: int):
    await execute(env, "DELETE FROM document_assets WHERE id = ?", asset_id)


async def create_member_record(env, *, name: str, role: str, part: str, contact: str, is_active: int):
    result = await execute(
        env,
        """
        INSERT INTO members (name, role, part, contact, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        name,
        role,
        part,
        contact,
        is_active,
    )
    return result.get("meta", {}).get("last_row_id")


async def update_member_record(
    env, member_id: int, *, name: str, role: str, part: str, contact: str, is_active: int
):
    await execute(
        env,
        """
        UPDATE members
        SET name = ?, role = ?, part = ?, contact = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        name,
        role,
        part,
        contact,
        is_active,
        member_id,
    )


async def delete_member_record(env, member_id: int):
    await execute(
        env,
        "UPDATE wbs_tasks SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
        member_id,
    )
    await execute(
        env,
        "UPDATE schedules SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
        member_id,
    )
    await execute(
        env,
        "UPDATE documents SET author_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE author_id = ?",
        member_id,
    )
    await execute(env, "DELETE FROM members WHERE id = ?", member_id)


async def create_schedule_record(
    env,
    *,
    title: str,
    description: str,
    start_date: str,
    end_date: str,
    assignee_id: int | None,
    wbs_task_id: int | None,
    schedule_type: str,
):
    result = await execute(
        env,
        """
        INSERT INTO schedules (
            title, description, start_date, end_date, assignee_id, wbs_task_id, schedule_type, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        title,
        description,
        start_date,
        end_date,
        assignee_id,
        wbs_task_id,
        schedule_type,
    )
    return result.get("meta", {}).get("last_row_id")


async def update_schedule_record(
    env,
    schedule_id: int,
    *,
    title: str,
    description: str,
    start_date: str,
    end_date: str,
    assignee_id: int | None,
    wbs_task_id: int | None,
    schedule_type: str,
):
    await execute(
        env,
        """
        UPDATE schedules
        SET title = ?, description = ?, start_date = ?, end_date = ?,
            assignee_id = ?, wbs_task_id = ?, schedule_type = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        title,
        description,
        start_date,
        end_date,
        assignee_id,
        wbs_task_id,
        schedule_type,
        schedule_id,
    )


async def delete_schedule_record(env, schedule_id: int):
    await execute(env, "DELETE FROM schedules WHERE id = ?", schedule_id)


async def create_wbs_record(
    env,
    *,
    parent_id: int | None,
    title: str,
    description: str,
    assignee_id: int | None,
    platform: str,
    status: str,
    priority: str,
    start_date: str | None,
    due_date: str | None,
    completed_date: str | None,
    progress: int,
    notes: str,
):
    result = await execute(
        env,
        """
        INSERT INTO wbs_tasks (
            parent_id, title, description, assignee_id, platform, status, priority,
            start_date, due_date, completed_date, progress, notes, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        parent_id,
        title,
        description,
        assignee_id,
        platform,
        status,
        priority,
        start_date,
        due_date,
        completed_date,
        progress,
        notes,
    )
    return result.get("meta", {}).get("last_row_id")


async def sync_wbs_task_documents(env, task_id: int, document_ids: list[int]):
    await execute(env, "DELETE FROM task_documents WHERE task_id = ?", task_id)
    for document_id in sorted(set(document_ids)):
        await execute(
            env,
            "INSERT OR IGNORE INTO task_documents (task_id, document_id) VALUES (?, ?)",
            task_id,
            document_id,
        )


async def update_wbs_record(
    env,
    task_id: int,
    *,
    parent_id: int | None,
    title: str,
    description: str,
    assignee_id: int | None,
    platform: str,
    status: str,
    priority: str,
    start_date: str | None,
    due_date: str | None,
    completed_date: str | None,
    progress: int,
    notes: str,
):
    await execute(
        env,
        """
        UPDATE wbs_tasks
        SET parent_id = ?, title = ?, description = ?, assignee_id = ?, platform = ?,
            status = ?, priority = ?, start_date = ?, due_date = ?,
            completed_date = ?, progress = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        parent_id,
        title,
        description,
        assignee_id,
        platform,
        status,
        priority,
        start_date,
        due_date,
        completed_date,
        progress,
        notes,
        task_id,
    )


async def delete_wbs_record(env, task_id: int):
    await execute(env, "DELETE FROM task_documents WHERE task_id = ?", task_id)
    await execute(
        env,
        "UPDATE schedules SET wbs_task_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE wbs_task_id = ?",
        task_id,
    )
    await execute(env, "UPDATE wbs_tasks SET parent_id = NULL WHERE parent_id = ?", task_id)
    await execute(env, "DELETE FROM wbs_tasks WHERE id = ?", task_id)
