from __future__ import annotations


class AssetGroupError(ValueError):
    pass


def normalize_asset_group_path(path: str):
    parts = [segment.strip() for segment in str(path or "").replace("\\", "/").split("/") if segment.strip()]
    return "/".join(parts)


def _asset_group_ancestors(path: str):
    normalized = normalize_asset_group_path(path)
    if not normalized:
        return []
    parts = normalized.split("/")
    return ["/".join(parts[: index + 1]) for index in range(len(parts))]


def _asset_group_like_params(path: str):
    normalized = normalize_asset_group_path(path)
    return normalized, f"{normalized}/%"


def list_assets(
    db,
    *,
    search: str,
    asset_type: str,
    category: str,
    status: str,
    tag: str,
    include_hidden: bool,
    updated_since: str,
    limit: int,
    offset: int,
):
    clauses = []
    params: list[str] = []
    joins = ["LEFT JOIN members m ON m.id = a.created_by"]
    count_joins: list[str] = []

    if not include_hidden:
        clauses.append("a.is_hidden = 0")
    if search:
        clauses.append(
            "(a.title LIKE ? OR a.original_filename LIKE ? OR a.category LIKE ? OR a.notes LIKE ?)"
        )
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])
    if asset_type:
        clauses.append("a.asset_type = ?")
        params.append(asset_type)
    if category:
        if category == "미분류":
            clauses.append("COALESCE(a.category, '') = ''")
        else:
            clauses.append("a.category = ?")
            params.append(category)
    if status:
        clauses.append("a.status = ?")
        params.append(status)
    if updated_since:
        clauses.append("a.updated_at >= ?")
        params.append(updated_since)
    if tag:
        joins.append("JOIN asset_tags at_filter ON at_filter.asset_id = a.id")
        count_joins.append("JOIN asset_tags at_filter ON at_filter.asset_id = a.id")
        clauses.append("at_filter.tag = ?")
        params.append(tag)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    if count_joins:
        total_count = db.execute(
            f"""
            SELECT COUNT(DISTINCT a.id) AS count
            FROM assets a
            {' '.join(count_joins)}
            {where_sql}
            """,
            params,
        ).fetchone()["count"]
    else:
        total_count = db.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM assets a
            {where_sql}
            """,
            params,
        ).fetchone()["count"]

    rows = db.execute(
        f"""
        SELECT DISTINCT
            a.*,
            m.name AS created_by_name
        FROM assets a
        {' '.join(joins)}
        {where_sql}
        ORDER BY a.updated_at DESC, a.id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()
    return total_count, rows


def fetch_asset(asset_id: int, db):
    return db.execute(
        """
        SELECT a.*, m.name AS created_by_name
        FROM assets a
        LEFT JOIN members m ON m.id = a.created_by
        WHERE a.id = ?
        """,
        (asset_id,),
    ).fetchone()


def fetch_asset_with_tags(asset_id: int, db):
    asset = fetch_asset(asset_id, db)
    if not asset:
        return None, []
    tag_rows = db.execute(
        "SELECT tag FROM asset_tags WHERE asset_id = ? ORDER BY tag COLLATE NOCASE ASC",
        (asset_id,),
    ).fetchall()
    return asset, [row["tag"] for row in tag_rows]


def fetch_asset_tag_options(db):
    return db.execute(
        """
        SELECT tag, COUNT(*) AS usage_count
        FROM asset_tags
        GROUP BY tag
        ORDER BY tag COLLATE NOCASE ASC
        """
    ).fetchall()


def fetch_asset_type_options(db):
    return db.execute(
        """
        SELECT DISTINCT asset_type
        FROM assets
        WHERE COALESCE(asset_type, '') != ''
        ORDER BY asset_type COLLATE NOCASE ASC
        """
    ).fetchall()


def fetch_category_options(db, *, include_hidden: bool):
    where_sql = "" if include_hidden else "WHERE COALESCE(is_hidden, 0) = 0"
    return db.execute(
        f"""
        SELECT
            CASE
                WHEN COALESCE(category, '') = '' THEN '미분류'
                ELSE category
            END AS category,
            COUNT(*) AS asset_count,
            MAX(updated_at) AS last_updated_at
        FROM assets
        {where_sql}
        GROUP BY CASE
            WHEN COALESCE(category, '') = '' THEN '미분류'
            ELSE category
        END
        ORDER BY category COLLATE NOCASE ASC
        """
    ).fetchall()


def fetch_asset_groups(db, *, include_hidden: bool):
    group_rows = db.execute(
        """
        SELECT path, created_at
        FROM asset_groups
        ORDER BY path COLLATE NOCASE ASC
        """
    ).fetchall()
    where_sql = "" if include_hidden else "WHERE COALESCE(is_hidden, 0) = 0"
    asset_rows = db.execute(
        f"""
        SELECT
            COALESCE(category, '') AS category,
            COUNT(*) AS asset_count,
            MAX(updated_at) AS last_updated_at
        FROM assets
        {where_sql}
        GROUP BY COALESCE(category, '')
        """
    ).fetchall()

    by_path: dict[str, dict] = {}
    for row in group_rows:
        path = normalize_asset_group_path(row["path"])
        if not path:
            continue
        by_path[path] = {
            "path": path,
            "direct_asset_count": 0,
            "last_updated_at": None,
            "is_explicit": 1,
        }

    for row in asset_rows:
        category = normalize_asset_group_path(row["category"])
        if not category:
            continue
        for ancestor in _asset_group_ancestors(category):
            target = by_path.setdefault(
                ancestor,
                {
                    "path": ancestor,
                    "direct_asset_count": 0,
                    "last_updated_at": None,
                    "is_explicit": 0,
                },
            )
            if ancestor == category:
                target["direct_asset_count"] = int(row["asset_count"] or 0)
                target["last_updated_at"] = row["last_updated_at"]

    return sorted(by_path.values(), key=lambda item: item["path"].lower())


def ensure_asset_group(db, path: str):
    normalized = normalize_asset_group_path(path)
    if not normalized:
        return ""
    for ancestor in _asset_group_ancestors(normalized):
        db.execute(
            "INSERT OR IGNORE INTO asset_groups (path) VALUES (?)",
            (ancestor,),
        )
    return normalized


def rename_asset_group(db, path: str, new_name: str):
    normalized_path = normalize_asset_group_path(path)
    normalized_name = normalize_asset_group_path(new_name)
    if not normalized_path:
        raise AssetGroupError("이름을 바꿀 폴더를 선택해주세요.")
    if not normalized_name or "/" in normalized_name:
        raise AssetGroupError("폴더 이름에는 단일 이름만 입력해주세요.")

    parent_path = "/".join(normalized_path.split("/")[:-1])
    target_path = "/".join(part for part in [parent_path, normalized_name] if part)
    if target_path == normalized_path:
        return normalized_path

    exists = db.execute(
        "SELECT 1 FROM asset_groups WHERE path = ?",
        (normalized_path,),
    ).fetchone()
    if not exists:
        raise AssetGroupError("선택한 폴더를 찾을 수 없습니다.")

    conflict = db.execute(
        "SELECT 1 FROM asset_groups WHERE path = ?",
        (target_path,),
    ).fetchone()
    if conflict:
        raise AssetGroupError("같은 위치에 동일한 폴더명이 이미 있습니다.")

    if parent_path:
        ensure_asset_group(db, parent_path)
    source_exact, source_like = _asset_group_like_params(normalized_path)
    descendant_rows = db.execute(
        """
        SELECT path
        FROM asset_groups
        WHERE path = ? OR path LIKE ?
        ORDER BY length(path) ASC, path COLLATE NOCASE ASC
        """,
        (source_exact, source_like),
    ).fetchall()

    temp_prefix = f"__rename__/{target_path}"
    for row in descendant_rows:
        current_path = row["path"]
        suffix = current_path[len(normalized_path) :]
        db.execute(
            "UPDATE asset_groups SET path = ? WHERE path = ?",
            (f"{temp_prefix}{suffix}", current_path),
        )

    temp_exact, temp_like = _asset_group_like_params(temp_prefix)
    staged_rows = db.execute(
        """
        SELECT path
        FROM asset_groups
        WHERE path = ? OR path LIKE ?
        ORDER BY length(path) ASC, path COLLATE NOCASE ASC
        """,
        (temp_exact, temp_like),
    ).fetchall()
    for row in staged_rows:
        current_path = row["path"]
        suffix = current_path[len(temp_prefix) :]
        db.execute(
            "UPDATE asset_groups SET path = ? WHERE path = ?",
            (f"{target_path}{suffix}", current_path),
        )

    asset_rows = db.execute(
        """
        SELECT id, category
        FROM assets
        WHERE category = ? OR category LIKE ?
        """,
        (source_exact, source_like),
    ).fetchall()
    for row in asset_rows:
        current_category = normalize_asset_group_path(row["category"])
        suffix = current_category[len(normalized_path) :]
        db.execute(
            """
            UPDATE assets
            SET category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (f"{target_path}{suffix}", row["id"]),
        )

    return target_path


def delete_asset_group(db, path: str):
    normalized = normalize_asset_group_path(path)
    if not normalized:
        raise AssetGroupError("삭제할 폴더를 선택해주세요.")
    exact, like = _asset_group_like_params(normalized)
    asset_count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM assets
        WHERE category = ? OR category LIKE ?
        """,
        (exact, like),
    ).fetchone()["count"]
    if asset_count:
        raise AssetGroupError("하위 Asset이 남아 있는 폴더는 삭제할 수 없습니다.")

    db.execute(
        "DELETE FROM asset_groups WHERE path = ? OR path LIKE ?",
        (exact, like),
    )


def create_asset(db, data):
    data["category"] = ensure_asset_group(db, data["category"])
    cursor = db.execute(
        """
        INSERT INTO assets (
            title, asset_type, category, file_name, original_filename, object_key, url,
            content_type, size, checksum, status, is_hidden, created_by, notes, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            data["title"],
            data["asset_type"],
            data["category"],
            data["file_name"],
            data["original_filename"],
            data["object_key"],
            data["url"],
            data["content_type"],
            data["size"],
            data["checksum"],
            data["status"],
            data["is_hidden"],
            data["created_by"],
            data["notes"],
        ),
    )
    return cursor.lastrowid


def update_asset(db, asset_id: int, data):
    data["category"] = ensure_asset_group(db, data["category"])
    db.execute(
        """
        UPDATE assets
        SET title = ?, asset_type = ?, category = ?, file_name = ?, original_filename = ?,
            object_key = ?, url = ?, content_type = ?, size = ?, checksum = ?,
            status = ?, is_hidden = ?, created_by = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            data["title"],
            data["asset_type"],
            data["category"],
            data["file_name"],
            data["original_filename"],
            data["object_key"],
            data["url"],
            data["content_type"],
            data["size"],
            data["checksum"],
            data["status"],
            data["is_hidden"],
            data["created_by"],
            data["notes"],
            asset_id,
        ),
    )


def delete_asset(db, asset_id: int):
    db.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))
    db.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
