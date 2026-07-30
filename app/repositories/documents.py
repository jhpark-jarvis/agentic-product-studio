from __future__ import annotations


def fetch_document_folders(db, doc_type: str | None = None):
    if doc_type:
        return db.execute(
            """
            SELECT f.id, f.doc_type, f.name, COUNT(d.id) AS document_count
            FROM document_folders f
            LEFT JOIN documents d ON d.folder_id = f.id
            WHERE f.doc_type = ?
            GROUP BY f.id, f.doc_type, f.name
            ORDER BY f.name COLLATE NOCASE ASC
            """,
            (doc_type,),
        ).fetchall()

    return db.execute(
        """
        SELECT f.id, f.doc_type, f.name, COUNT(d.id) AS document_count
        FROM document_folders f
        LEFT JOIN documents d ON d.folder_id = f.id
        GROUP BY f.id, f.doc_type, f.name
        ORDER BY f.doc_type COLLATE NOCASE ASC, f.name COLLATE NOCASE ASC
        """
    ).fetchall()


def fetch_folder(db, folder_id: int):
    return db.execute(
        """
        SELECT id, doc_type, name
        FROM document_folders
        WHERE id = ?
        """,
        (folder_id,),
    ).fetchone()


def create_document_folder(db, doc_type: str, name: str):
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise ValueError("폴더 이름을 입력해주세요.")

    existing = db.execute(
        "SELECT id FROM document_folders WHERE doc_type = ? AND lower(name) = lower(?)",
        (doc_type, normalized_name),
    ).fetchone()
    if existing:
        raise ValueError("같은 유형에 동일한 폴더가 이미 있습니다.")

    cursor = db.execute(
        "INSERT INTO document_folders (doc_type, name) VALUES (?, ?)",
        (doc_type, normalized_name),
    )
    return fetch_folder(db, cursor.lastrowid)


def update_document_folder_definition(db, folder_id: int, doc_type: str, name: str):
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise ValueError("폴더 이름을 입력해주세요.")
    if not fetch_folder(db, folder_id):
        raise ValueError("선택한 폴더를 찾을 수 없습니다.")

    existing = db.execute(
        """
        SELECT id
        FROM document_folders
        WHERE doc_type = ? AND lower(name) = lower(?) AND id != ?
        """,
        (doc_type, normalized_name, folder_id),
    ).fetchone()
    if existing:
        raise ValueError("같은 유형에 동일한 폴더가 이미 있습니다.")

    db.execute(
        "UPDATE document_folders SET doc_type = ?, name = ? WHERE id = ?",
        (doc_type, normalized_name, folder_id),
    )
    return fetch_folder(db, folder_id)


def delete_document_folder(db, folder_id: int):
    folder = fetch_folder(db, folder_id)
    if not folder:
        raise ValueError("선택한 폴더를 찾을 수 없습니다.")
    document_count = db.execute(
        "SELECT COUNT(*) AS count FROM documents WHERE folder_id = ?",
        (folder_id,),
    ).fetchone()["count"]
    if document_count:
        raise ValueError("문서가 연결된 폴더는 삭제할 수 없습니다. 먼저 문서를 다른 폴더로 이동해주세요.")
    db.execute("DELETE FROM document_folders WHERE id = ?", (folder_id,))


def fetch_document_with_relations(db, document_id: int):
    document = db.execute(
        """
        SELECT d.*, m.name AS author_name, f.name AS folder_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
        LEFT JOIN document_folders f ON f.id = d.folder_id
        WHERE d.id = ?
        """,
        (document_id,),
    ).fetchone()
    if not document:
        return None, [], []

    related_tasks = db.execute(
        """
        SELECT t.id, t.title, t.status, t.priority
        FROM task_documents td
        JOIN wbs_tasks t ON t.id = td.task_id
        WHERE td.document_id = ?
        ORDER BY t.updated_at DESC, t.id DESC
        """,
        (document_id,),
    ).fetchall()
    tag_rows = db.execute(
        "SELECT tag FROM document_tags WHERE document_id = ? ORDER BY tag COLLATE NOCASE ASC",
        (document_id,),
    ).fetchall()
    return document, related_tasks, [row["tag"] for row in tag_rows]


def fetch_documents_by_ids(db, document_ids: list[int]):
    normalized_ids = sorted({int(document_id) for document_id in document_ids if int(document_id) > 0})
    if not normalized_ids:
        return []

    placeholders = ", ".join("?" for _ in normalized_ids)
    return db.execute(
        f"""
        SELECT d.*, m.name AS author_name, f.name AS folder_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
        LEFT JOIN document_folders f ON f.id = d.folder_id
        WHERE d.id IN ({placeholders})
        ORDER BY d.updated_at DESC, d.id DESC
        """,
        normalized_ids,
    ).fetchall()


def search_documents_for_link(db, *, keyword: str, limit: int = 10):
    normalized = (keyword or "").strip()
    if not normalized:
        return []

    return db.execute(
        """
        SELECT
            d.id,
            d.title,
            d.doc_type,
            d.is_hidden,
            d.updated_at,
            f.name AS folder_name
        FROM documents d
        LEFT JOIN document_folders f ON f.id = d.folder_id
        WHERE d.title LIKE ?
        ORDER BY
            CASE WHEN d.is_hidden = 1 THEN 0 ELSE 1 END DESC,
            d.updated_at DESC,
            d.id DESC
        LIMIT ?
        """,
        (f"%{normalized}%", limit),
    ).fetchall()


def list_documents(
    db,
    *,
    search: str,
    doc_type: str,
    tag: str,
    folder_id: str,
    include_hidden: bool,
    limit: int,
    offset: int,
):
    clauses = []
    params: list[str] = []
    joins = ["LEFT JOIN members m ON m.id = d.author_id", "LEFT JOIN document_folders f ON f.id = d.folder_id"]
    count_joins: list[str] = []

    if not include_hidden:
        clauses.append("d.is_hidden = 0")

    if search:
        clauses.append("d.title LIKE ?")
        params.append(f"%{search}%")
    if doc_type:
        clauses.append("d.doc_type = ?")
        params.append(doc_type)
    if tag:
        joins.append("JOIN document_tags dt_filter ON dt_filter.document_id = d.id")
        count_joins.append("JOIN document_tags dt_filter ON dt_filter.document_id = d.id")
        clauses.append("dt_filter.tag = ?")
        params.append(tag)
    if folder_id and folder_id.isdigit():
        clauses.append("d.folder_id = ?")
        params.append(folder_id)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    if count_joins:
        count_sql = f"""
        SELECT COUNT(DISTINCT d.id) AS count
        FROM documents d
        {' '.join(count_joins)}
        {where_sql}
        """
    else:
        count_sql = f"""
        SELECT COUNT(*) AS count
        FROM documents d
        {where_sql}
        """
    total_count = db.execute(count_sql, params).fetchone()["count"]

    rows = db.execute(
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
        [*params, limit, offset],
    ).fetchall()
    return total_count, rows


def fetch_tag_options(db):
    return db.execute(
        """
        SELECT tag, COUNT(*) AS usage_count
        FROM document_tags
        GROUP BY tag
        ORDER BY tag COLLATE NOCASE ASC
        """
    ).fetchall()


def create_document(db, data, folder_id):
    cursor = db.execute(
        """
        INSERT INTO documents (
            title, doc_type, folder_id, is_hidden, content, author_id, tags, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            data["title"],
            data["doc_type"],
            folder_id,
            data["is_hidden"],
            data["content"],
            data["author_id"],
            data["tags"],
        ),
    )
    return cursor.lastrowid


def update_document(db, document_id, data, folder_id):
    db.execute(
        """
        UPDATE documents
        SET title = ?, doc_type = ?, folder_id = ?, is_hidden = ?,
            content = ?, author_id = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            data["title"],
            data["doc_type"],
            folder_id,
            data["is_hidden"],
            data["content"],
            data["author_id"],
            data["tags"],
            document_id,
        ),
    )


def bulk_set_hidden(db, document_ids: list[int], is_hidden: int):
    normalized_ids = sorted({int(document_id) for document_id in document_ids if int(document_id) > 0})
    if not normalized_ids:
        return 0

    placeholders = ", ".join("?" for _ in normalized_ids)
    cursor = db.execute(
        f"""
        UPDATE documents
        SET is_hidden = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id IN ({placeholders})
        """,
        [is_hidden, *normalized_ids],
    )
    return cursor.rowcount


def delete_document(db, document_id):
    db.execute("DELETE FROM document_assets WHERE document_id = ?", (document_id,))
    db.execute("DELETE FROM task_documents WHERE document_id = ?", (document_id,))
    db.execute("DELETE FROM document_tags WHERE document_id = ?", (document_id,))
    db.execute("DELETE FROM documents WHERE id = ?", (document_id,))


def update_document_folder(db, document_id, doc_type, folder_id):
    db.execute(
        """
        UPDATE documents
        SET doc_type = ?, folder_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (doc_type, folder_id, document_id),
    )
