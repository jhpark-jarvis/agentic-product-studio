from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app

from ..db import (
    assign_draft_assets_to_document,
    ensure_document_folder,
    get_db,
    sync_asset_tags as sync_asset_tags_local,
    sync_document_tags as sync_document_tags_local,
    sync_task_documents as sync_task_documents_for_task_local,
    sync_task_documents_for_document as sync_task_documents_for_document_local,
)
from .assets import AssetGroupError, normalize_asset_group_path
from .provider import RepositoryProvider


class D1RepositoryError(RuntimeError):
    pass


class D1WriteNotSupportedError(NotImplementedError):
    pass


_READ_CACHE: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str):
    cached = _READ_CACHE.get(key)
    if not cached:
        return None
    expires_at, value = cached
    if expires_at < monotonic():
        _READ_CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value, ttl_seconds: float = 30.0):
    _READ_CACHE[key] = (monotonic() + ttl_seconds, value)
    return value


def _cache_invalidate(*prefixes: str):
    if not prefixes:
        _READ_CACHE.clear()
        return
    for key in list(_READ_CACHE.keys()):
        if any(key.startswith(prefix) for prefix in prefixes):
            _READ_CACHE.pop(key, None)


class D1RestClient:
    def __init__(self, *, account_id: str, database_id: str, api_token: str):
        if not account_id:
            raise D1RepositoryError("CLOUDFLARE_ACCOUNT_ID is required for D1 repository.")
        if not database_id:
            raise D1RepositoryError("D1_DATABASE_ID is required for D1 repository.")
        resolved_token = api_token or _load_wrangler_oauth_token()
        if not resolved_token:
            raise D1RepositoryError("CLOUDFLARE_API_TOKEN is required for D1 repository.")

        self.account_id = account_id
        self.database_id = database_id
        self.api_token = resolved_token

    @property
    def _query_url(self) -> str:
        return (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/d1/database/{self.database_id}/query"
        )

    def query(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None):
        payload = {"sql": sql}
        if params:
            payload["params"] = list(params)

        request = Request(
            self._query_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise D1RepositoryError(f"D1 API request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise D1RepositoryError(f"D1 API connection failed: {exc}") from exc

        if not body.get("success", False):
            raise D1RepositoryError(f"D1 API unsuccessful response: {body}")

        results = body.get("result") or []
        if not results:
            return {"results": [], "meta": {}, "success": True}

        result = results[0]
        if not result.get("success", False):
            raise D1RepositoryError(f"D1 query failed: {body}")
        return result

    def query_rows(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None):
        return self.query(sql, params).get("results", [])

    def query_first(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None):
        rows = self.query_rows(sql, params)
        return rows[0] if rows else None


def _load_wrangler_oauth_token():
    config_path = Path.home() / "AppData/Roaming/xdg.config/.wrangler/config/default.toml"
    if not config_path.exists():
        return ""

    for line in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("oauth_token = "):
            return stripped.split("=", 1)[1].strip().strip('"')
    return ""


def _raise_write_not_supported():
    raise D1WriteNotSupportedError(
        "D1 provider is currently read-only. Write operations stay on the SQLite backend for now."
    )


def _normalize_folder_name(folder_name: str):
    return (folder_name or "").strip()


def _normalize_tags(tags_text: str):
    tags = []
    for raw in (tags_text or "").split(","):
        tag = raw.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _shadow_upsert_folder(folder_id: int, doc_type: str, folder_name: str):
    local_db = get_db()
    normalized_name = _normalize_folder_name(folder_name)
    existing = local_db.execute(
        "SELECT id FROM document_folders WHERE id = ?",
        (folder_id,),
    ).fetchone()
    if existing:
        local_db.execute(
            """
            UPDATE document_folders
            SET doc_type = ?, name = ?
            WHERE id = ?
            """,
            (doc_type, normalized_name, folder_id),
        )
        return
    local_db.execute(
        """
        INSERT INTO document_folders (id, doc_type, name)
        VALUES (?, ?, ?)
        """,
        (folder_id, doc_type, normalized_name),
    )


def _shadow_upsert_document(document_id: int, data, folder_id):
    local_db = get_db()
    existing = local_db.execute(
        "SELECT id FROM documents WHERE id = ?",
        (document_id,),
    ).fetchone()
    params = (
        data["title"],
        data["doc_type"],
        folder_id,
        data["is_hidden"],
        data["content"],
        data["author_id"],
        data["tags"],
        document_id,
    )
    if existing:
        local_db.execute(
            """
            UPDATE documents
            SET title = ?, doc_type = ?, folder_id = ?, is_hidden = ?,
                content = ?, author_id = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            params,
        )
        return
    local_db.execute(
        """
        INSERT INTO documents (
            id, title, doc_type, folder_id, is_hidden, content, author_id, tags, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            document_id,
            data["title"],
            data["doc_type"],
            folder_id,
            data["is_hidden"],
            data["content"],
            data["author_id"],
            data["tags"],
        ),
    )


def _shadow_delete_document(document_id: int):
    local_db = get_db()
    local_db.execute("DELETE FROM document_assets WHERE document_id = ?", (document_id,))
    local_db.execute("DELETE FROM task_documents WHERE document_id = ?", (document_id,))
    local_db.execute("DELETE FROM document_tags WHERE document_id = ?", (document_id,))
    local_db.execute("DELETE FROM documents WHERE id = ?", (document_id,))


def _shadow_upsert_document_asset(
    asset_id: int,
    *,
    document_id: int | None,
    draft_key: str | None,
    object_key: str,
    url: str,
    original_filename: str,
    content_type: str,
    size: int,
):
    local_db = get_db()
    existing = local_db.execute(
        "SELECT id FROM document_assets WHERE id = ?",
        (asset_id,),
    ).fetchone()
    params = (
        document_id,
        draft_key,
        object_key,
        url,
        original_filename,
        content_type,
        size,
        asset_id,
    )
    if existing:
        local_db.execute(
            """
            UPDATE document_assets
            SET document_id = ?, draft_key = ?, object_key = ?, url = ?,
                original_filename = ?, content_type = ?, size = ?
            WHERE id = ?
            """,
            params,
        )
        return
    local_db.execute(
        """
        INSERT INTO document_assets (
            id, document_id, draft_key, object_key, url, original_filename, content_type, size, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            asset_id,
            document_id,
            draft_key,
            object_key,
            url,
            original_filename,
            content_type,
            size,
        ),
    )


def _shadow_delete_document_asset(asset_id: int):
    get_db().execute("DELETE FROM document_assets WHERE id = ?", (asset_id,))


def _shadow_upsert_asset(asset_id: int, data):
    local_db = get_db()
    existing = local_db.execute("SELECT id FROM assets WHERE id = ?", (asset_id,)).fetchone()
    params = (
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
    )
    if existing:
        local_db.execute(
            """
            UPDATE assets
            SET title = ?, asset_type = ?, category = ?, file_name = ?, original_filename = ?,
                object_key = ?, url = ?, content_type = ?, size = ?, checksum = ?,
                status = ?, is_hidden = ?, created_by = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            params,
        )
        return
    local_db.execute(
        """
        INSERT INTO assets (
            id, title, asset_type, category, file_name, original_filename, object_key, url,
            content_type, size, checksum, status, is_hidden, created_by, notes, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            asset_id,
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


def _shadow_delete_asset(asset_id: int):
    local_db = get_db()
    local_db.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))
    local_db.execute("DELETE FROM assets WHERE id = ?", (asset_id,))


def _shadow_ensure_asset_group(path: str):
    local_db = get_db()
    normalized = normalize_asset_group_path(path)
    if not normalized:
        return ""
    parts = normalized.split("/")
    for index in range(len(parts)):
        ancestor = "/".join(parts[: index + 1])
        local_db.execute(
            "INSERT OR IGNORE INTO asset_groups (path) VALUES (?)",
            (ancestor,),
        )
    return normalized


def _shadow_rename_asset_group(path: str, new_name: str):
    from . import assets as asset_queries

    return asset_queries.rename_asset_group(get_db(), path, new_name)


def _shadow_delete_asset_group(path: str):
    from . import assets as asset_queries

    asset_queries.delete_asset_group(get_db(), path)


def _shadow_upsert_member(member_id: int, data):
    local_db = get_db()
    existing = local_db.execute("SELECT id FROM members WHERE id = ?", (member_id,)).fetchone()
    if existing:
        local_db.execute(
            """
            UPDATE members
            SET name = ?, role = ?, part = ?, contact = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (data["name"], data["role"], data["part"], data["contact"], data["is_active"], member_id),
        )
        return
    local_db.execute(
        """
        INSERT INTO members (id, name, role, part, contact, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (member_id, data["name"], data["role"], data["part"], data["contact"], data["is_active"]),
    )


def _shadow_delete_member(member_id: int):
    local_db = get_db()
    local_db.execute(
        "UPDATE wbs_tasks SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
        (member_id,),
    )
    local_db.execute(
        "UPDATE schedules SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
        (member_id,),
    )
    local_db.execute(
        "UPDATE documents SET author_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE author_id = ?",
        (member_id,),
    )
    local_db.execute("DELETE FROM members WHERE id = ?", (member_id,))


def _shadow_upsert_schedule(schedule_id: int, data):
    local_db = get_db()
    existing = local_db.execute("SELECT id FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    params = (
        data["title"],
        data["description"],
        data["start_date"],
        data["end_date"],
        data["assignee_id"],
        data["wbs_task_id"],
        data["schedule_type"],
        schedule_id,
    )
    if existing:
        local_db.execute(
            """
            UPDATE schedules
            SET title = ?, description = ?, start_date = ?, end_date = ?,
                assignee_id = ?, wbs_task_id = ?, schedule_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            params,
        )
        return
    local_db.execute(
        """
        INSERT INTO schedules (
            id, title, description, start_date, end_date, assignee_id, wbs_task_id, schedule_type, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            schedule_id,
            data["title"],
            data["description"],
            data["start_date"],
            data["end_date"],
            data["assignee_id"],
            data["wbs_task_id"],
            data["schedule_type"],
        ),
    )


def _shadow_delete_schedule(schedule_id: int):
    get_db().execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))


def _shadow_upsert_wbs_task(task_id: int, data):
    local_db = get_db()
    existing = local_db.execute("SELECT id FROM wbs_tasks WHERE id = ?", (task_id,)).fetchone()
    params = (
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
    )
    if existing:
        local_db.execute(
            """
            UPDATE wbs_tasks
            SET parent_id = ?, title = ?, description = ?, assignee_id = ?, platform = ?,
                status = ?, priority = ?, start_date = ?, due_date = ?,
                completed_date = ?, progress = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            params,
        )
        return
    local_db.execute(
        """
        INSERT INTO wbs_tasks (
            id, parent_id, title, description, assignee_id, platform, status, priority,
            start_date, due_date, completed_date, progress, notes, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            task_id,
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


def _shadow_delete_wbs_task(task_id: int):
    local_db = get_db()
    local_db.execute("DELETE FROM task_documents WHERE task_id = ?", (task_id,))
    local_db.execute(
        "UPDATE schedules SET wbs_task_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE wbs_task_id = ?",
        (task_id,),
    )
    local_db.execute("UPDATE wbs_tasks SET parent_id = NULL WHERE parent_id = ?", (task_id,))
    local_db.execute("DELETE FROM wbs_tasks WHERE id = ?", (task_id,))


@dataclass
class D1CommonRepository:
    client: D1RestClient

    def fetch_active_members(self):
        cache_key = "common:active_members"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT id, name, role, part
            FROM members
            WHERE is_active = 1
            ORDER BY name COLLATE NOCASE ASC
            """
            ),
        )

    def fetch_document_link_options(self):
        cache_key = "common:document_link_options"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT id, title, doc_type, is_hidden
            FROM documents
            ORDER BY is_hidden ASC, updated_at DESC, title COLLATE NOCASE ASC
            """
            ),
        )

    def fetch_task_link_options(self):
        cache_key = "common:task_link_options"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT id, title, status
            FROM wbs_tasks
            ORDER BY updated_at DESC, id DESC
            """
            ),
        )

    def fetch_parent_task_options(self, exclude_task_id: int | None = None):
        cache_key = f"common:parent_task_options:{exclude_task_id if exclude_task_id is not None else 'all'}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        if exclude_task_id is None:
            return _cache_set(
                cache_key,
                self.client.query_rows(
                    "SELECT id, title FROM wbs_tasks ORDER BY created_at ASC, id ASC"
                ),
            )
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT id, title
            FROM wbs_tasks
            WHERE id != ?
            ORDER BY created_at ASC, id ASC
            """,
            [exclude_task_id],
            ),
        )


@dataclass
class D1DocumentsRepository:
    client: D1RestClient

    def fetch_document_folders(self, doc_type: str | None = None):
        cache_key = f"documents:folders:{doc_type or '*'}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        if doc_type:
            return _cache_set(
                cache_key,
                self.client.query_rows(
                """
                SELECT id, doc_type, name
                FROM document_folders
                WHERE doc_type = ?
                ORDER BY name COLLATE NOCASE ASC
                """,
                [doc_type],
                ),
            )
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT id, doc_type, name
            FROM document_folders
            ORDER BY doc_type COLLATE NOCASE ASC, name COLLATE NOCASE ASC
            """
            ),
        )

    def fetch_folder(self, folder_id: int):
        return self.client.query_first(
            """
            SELECT id, doc_type, name
            FROM document_folders
            WHERE id = ?
            """,
            [folder_id],
        )

    def ensure_folder(self, doc_type: str, folder_name: str):
        normalized_name = _normalize_folder_name(folder_name)
        existing = self.client.query_first(
            """
            SELECT id, doc_type, name
            FROM document_folders
            WHERE doc_type = ? AND lower(name) = lower(?)
            """,
            [doc_type, normalized_name],
        )
        if existing:
            _shadow_upsert_folder(existing["id"], existing["doc_type"], existing["name"])
            return existing["id"]

        result = self.client.query(
            """
            INSERT INTO document_folders (doc_type, name, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            [doc_type, normalized_name],
        )
        folder_id = result.get("meta", {}).get("last_row_id")
        if folder_id is None:
            created = self.client.query_first(
                """
                SELECT id, doc_type, name
                FROM document_folders
                WHERE doc_type = ? AND lower(name) = lower(?)
                ORDER BY id DESC
                LIMIT 1
                """,
                [doc_type, normalized_name],
            )
            if not created:
                raise D1RepositoryError("Failed to create or resolve document folder in D1.")
            folder_id = created["id"]
            _shadow_upsert_folder(folder_id, created["doc_type"], created["name"])
            _cache_invalidate("documents:")
            return folder_id

        _shadow_upsert_folder(folder_id, doc_type, normalized_name)
        _cache_invalidate("documents:")
        return folder_id

    def fetch_document_with_relations(self, document_id: int):
        cache_key = f"documents:detail:{document_id}:relations"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        document = self.client.query_first(
            """
            SELECT d.*, m.name AS author_name, f.name AS folder_name
            FROM documents d
            LEFT JOIN members m ON m.id = d.author_id
            LEFT JOIN document_folders f ON f.id = d.folder_id
            WHERE d.id = ?
            """,
            [document_id],
        )
        if not document:
            return None, [], []

        related_tasks = self.client.query_rows(
            """
            SELECT t.id, t.title, t.status, t.priority
            FROM task_documents td
            JOIN wbs_tasks t ON t.id = td.task_id
            WHERE td.document_id = ?
            ORDER BY t.updated_at DESC, t.id DESC
            """,
            [document_id],
        )
        tag_rows = self.client.query_rows(
            """
            SELECT tag
            FROM document_tags
            WHERE document_id = ?
            ORDER BY tag COLLATE NOCASE ASC
            """,
            [document_id],
        )
        return _cache_set(cache_key, (document, related_tasks, [row["tag"] for row in tag_rows]))

    def fetch_documents_by_ids(self, document_ids: list[int]):
        normalized_ids = sorted({int(document_id) for document_id in document_ids if int(document_id) > 0})
        if not normalized_ids:
            return []

        placeholders = ", ".join("?" for _ in normalized_ids)
        return self.client.query_rows(
            f"""
            SELECT d.*, m.name AS author_name, f.name AS folder_name
            FROM documents d
            LEFT JOIN members m ON m.id = d.author_id
            LEFT JOIN document_folders f ON f.id = d.folder_id
            WHERE d.id IN ({placeholders})
            ORDER BY d.updated_at DESC, d.id DESC
            """,
            normalized_ids,
        )

    def search_documents_for_link(self, *, keyword: str, limit: int = 10):
        normalized = (keyword or "").strip()
        if not normalized:
            return []

        return self.client.query_rows(
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
            [f"%{normalized}%", limit],
        )

    def list_documents(
        self,
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
        params: list[Any] = []
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
            params.append(int(folder_id))

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
        total_count_row = self.client.query_first(count_sql, params)
        rows = self.client.query_rows(
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
        )
        return (total_count_row or {}).get("count", 0), rows

    def fetch_tag_options(self):
        cache_key = "documents:tag_options"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT tag, COUNT(*) AS usage_count
            FROM document_tags
            GROUP BY tag
            ORDER BY tag COLLATE NOCASE ASC
            """
            ),
        )

    def create_document(self, data, folder_id):
        result = self.client.query(
            """
            INSERT INTO documents (
                title, doc_type, folder_id, is_hidden, content, author_id, tags, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            [
                data["title"],
                data["doc_type"],
                folder_id,
                data["is_hidden"],
                data["content"],
                data["author_id"],
                data["tags"],
            ],
        )
        document_id = result.get("meta", {}).get("last_row_id")
        if document_id is None:
            raise D1RepositoryError("Failed to create document in D1.")
        _shadow_upsert_document(document_id, data, folder_id)
        _cache_invalidate(f"documents:detail:{document_id}", "documents:", "common:document_link_options", "dashboard:")
        return document_id

    def create_document_asset(
        self,
        *,
        document_id: int | None,
        draft_key: str | None,
        object_key: str,
        url: str,
        original_filename: str,
        content_type: str,
        size: int,
    ):
        result = self.client.query(
            """
            INSERT INTO document_assets (
                document_id, draft_key, object_key, url, original_filename, content_type, size, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [document_id, draft_key, object_key, url, original_filename, content_type, size],
        )
        asset_id = result.get("meta", {}).get("last_row_id")
        if asset_id is None:
            raise D1RepositoryError("Failed to create document asset in D1.")
        _shadow_upsert_document_asset(
            asset_id,
            document_id=document_id,
            draft_key=draft_key,
            object_key=object_key,
            url=url,
            original_filename=original_filename,
            content_type=content_type,
            size=size,
        )
        if document_id is not None:
            _cache_invalidate(f"documents:detail:{document_id}")
        _cache_invalidate("dashboard:")
        return asset_id

    def fetch_document_assets(self, document_id: int):
        cache_key = f"documents:detail:{document_id}:assets"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT id, document_id, object_key, url, original_filename, content_type, size, created_at
            FROM document_assets
            WHERE document_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            [document_id],
            ),
        )

    def fetch_document_asset(self, asset_id: int):
        return self.client.query_first(
            """
            SELECT id, document_id, draft_key, object_key, url, original_filename, content_type, size, created_at
            FROM document_assets
            WHERE id = ?
            """,
            [asset_id],
        )

    def assign_draft_assets(self, document_id: int, draft_key: str):
        if not draft_key:
            return
        self.client.query(
            """
            UPDATE document_assets
            SET document_id = ?, draft_key = NULL
            WHERE draft_key = ? AND document_id IS NULL
            """,
            [document_id, draft_key],
        )
        assign_draft_assets_to_document(get_db(), document_id, draft_key)
        _cache_invalidate(f"documents:detail:{document_id}")
        _cache_invalidate("dashboard:")

    def sync_document_tags(self, document_id: int, tags_text: str):
        self.client.query("DELETE FROM document_tags WHERE document_id = ?", [document_id])
        tags = _normalize_tags(tags_text)
        for tag in tags:
            self.client.query(
                "INSERT INTO document_tags (document_id, tag) VALUES (?, ?)",
                [document_id, tag],
            )
        sync_document_tags_local(get_db(), document_id, tags_text)
        _cache_invalidate(f"documents:detail:{document_id}", "documents:")

    def sync_task_documents(self, document_id: int, task_ids: list[int]):
        self.client.query("DELETE FROM task_documents WHERE document_id = ?", [document_id])
        for task_id in sorted(set(task_ids)):
            self.client.query(
                "INSERT OR IGNORE INTO task_documents (task_id, document_id) VALUES (?, ?)",
                [task_id, document_id],
            )
        sync_task_documents_for_document_local(get_db(), document_id, task_ids)
        _cache_invalidate(f"documents:detail:{document_id}")
        _cache_invalidate("dashboard:")

    def update_document(self, document_id, data, folder_id):
        self.client.query(
            """
            UPDATE documents
            SET title = ?, doc_type = ?, folder_id = ?, is_hidden = ?,
                content = ?, author_id = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [
                data["title"],
                data["doc_type"],
                folder_id,
                data["is_hidden"],
                data["content"],
                data["author_id"],
                data["tags"],
                document_id,
            ],
        )
        _shadow_upsert_document(document_id, data, folder_id)
        _cache_invalidate(f"documents:detail:{document_id}", "documents:", "common:document_link_options", "dashboard:")

    def bulk_set_hidden(self, document_ids: list[int], is_hidden: int):
        normalized_ids = sorted({int(document_id) for document_id in document_ids if int(document_id) > 0})
        if not normalized_ids:
            return 0

        placeholders = ", ".join("?" for _ in normalized_ids)
        self.client.query(
            f"""
            UPDATE documents
            SET is_hidden = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
            """,
            [is_hidden, *normalized_ids],
        )

        for document_id in normalized_ids:
            document = self.client.query_first(
                """
                SELECT title, content, author_id, tags, is_hidden, doc_type, folder_id
                FROM documents
                WHERE id = ?
                """,
                [document_id],
            )
            if document:
                _shadow_upsert_document(document_id, document, document.get("folder_id"))

        _cache_invalidate("documents:", "common:document_link_options", "dashboard:")
        for document_id in normalized_ids:
            _cache_invalidate(f"documents:detail:{document_id}")
        return len(normalized_ids)

    def delete_document(self, document_id):
        self.client.query("DELETE FROM document_assets WHERE document_id = ?", [document_id])
        self.client.query("DELETE FROM task_documents WHERE document_id = ?", [document_id])
        self.client.query("DELETE FROM document_tags WHERE document_id = ?", [document_id])
        self.client.query("DELETE FROM documents WHERE id = ?", [document_id])
        _shadow_delete_document(document_id)
        _cache_invalidate(f"documents:detail:{document_id}", "documents:", "common:document_link_options", "dashboard:")

    def delete_document_asset(self, asset_id: int):
        asset = self.fetch_document_asset(asset_id)
        self.client.query("DELETE FROM document_assets WHERE id = ?", [asset_id])
        _shadow_delete_document_asset(asset_id)
        if asset and asset.get("document_id") is not None:
            _cache_invalidate(f"documents:detail:{asset['document_id']}")
        _cache_invalidate("dashboard:")

    def update_document_folder(self, document_id, doc_type, folder_id):
        self.client.query(
            """
            UPDATE documents
            SET doc_type = ?, folder_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [doc_type, folder_id, document_id],
        )
        document = self.client.query_first(
            """
            SELECT title, content, author_id, tags, is_hidden, doc_type
            FROM documents
            WHERE id = ?
            """,
            [document_id],
        )
        if document:
            _shadow_upsert_document(document_id, document, folder_id)
        _cache_invalidate(f"documents:detail:{document_id}", "documents:", "common:document_link_options", "dashboard:")


@dataclass
class D1AssetsRepository:
    client: D1RestClient

    def list_assets(
        self,
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
        params: list[Any] = []
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
            total_count = self.client.query_first(
                f"""
                SELECT COUNT(DISTINCT a.id) AS count
                FROM assets a
                {' '.join(count_joins)}
                {where_sql}
                """,
                params,
            )["count"]
        else:
            total_count = self.client.query_first(
                f"""
                SELECT COUNT(*) AS count
                FROM assets a
                {where_sql}
                """,
                params,
            )["count"]

        rows = self.client.query_rows(
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
        )
        return total_count, rows

    def fetch_asset(self, asset_id: int):
        return self.client.query_first(
            """
            SELECT a.*, m.name AS created_by_name
            FROM assets a
            LEFT JOIN members m ON m.id = a.created_by
            WHERE a.id = ?
            """,
            [asset_id],
        )

    def fetch_asset_with_tags(self, asset_id: int):
        asset = self.fetch_asset(asset_id)
        if not asset:
            return None, []
        rows = self.client.query_rows(
            "SELECT tag FROM asset_tags WHERE asset_id = ? ORDER BY tag COLLATE NOCASE ASC",
            [asset_id],
        )
        return asset, [row["tag"] for row in rows]

    def fetch_tag_options(self):
        return self.client.query_rows(
            """
            SELECT tag, COUNT(*) AS usage_count
            FROM asset_tags
            GROUP BY tag
            ORDER BY tag COLLATE NOCASE ASC
            """
        )

    def fetch_asset_type_options(self):
        return self.client.query_rows(
            """
            SELECT DISTINCT asset_type
            FROM assets
            WHERE COALESCE(asset_type, '') != ''
            ORDER BY asset_type COLLATE NOCASE ASC
            """
        )

    def fetch_category_options(self, *, include_hidden: bool):
        where_sql = "" if include_hidden else "WHERE COALESCE(is_hidden, 0) = 0"
        return self.client.query_rows(
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
        )

    def fetch_asset_groups(self, *, include_hidden: bool):
        group_rows = self.client.query_rows(
            """
            SELECT path, created_at
            FROM asset_groups
            ORDER BY path COLLATE NOCASE ASC
            """
        )
        where_sql = "" if include_hidden else "WHERE COALESCE(is_hidden, 0) = 0"
        asset_rows = self.client.query_rows(
            f"""
            SELECT
                COALESCE(category, '') AS category,
                COUNT(*) AS asset_count,
                MAX(updated_at) AS last_updated_at
            FROM assets
            {where_sql}
            GROUP BY COALESCE(category, '')
            """
        )

        by_path: dict[str, dict[str, Any]] = {}
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
            parts = category.split("/")
            for index in range(len(parts)):
                ancestor = "/".join(parts[: index + 1])
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

    def create_asset_group(self, path: str):
        normalized = normalize_asset_group_path(path)
        if not normalized:
            return ""
        parts = normalized.split("/")
        for index in range(len(parts)):
            ancestor = "/".join(parts[: index + 1])
            self.client.query(
                "INSERT OR IGNORE INTO asset_groups (path) VALUES (?)",
                [ancestor],
            )
        _shadow_ensure_asset_group(normalized)
        _cache_invalidate("assets:")
        return normalized

    def rename_asset_group(self, path: str, new_name: str):
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

        existing = self.client.query_first(
            "SELECT path FROM asset_groups WHERE path = ?",
            [normalized_path],
        )
        if not existing:
            raise AssetGroupError("선택한 폴더를 찾을 수 없습니다.")

        direct_conflict = self.client.query_first(
            "SELECT path FROM asset_groups WHERE path = ?",
            [target_path],
        )
        if direct_conflict:
            raise AssetGroupError("같은 위치에 동일한 폴더명이 이미 있습니다.")

        if parent_path:
            self.create_asset_group(parent_path)
        descendants = self.client.query_rows(
            """
            SELECT path
            FROM asset_groups
            WHERE path = ? OR path LIKE ?
            ORDER BY length(path) ASC, path COLLATE NOCASE ASC
            """,
            [normalized_path, f"{normalized_path}/%"],
        )

        temp_prefix = f"__rename__/{target_path}"
        for row in descendants:
            current_path = row["path"]
            suffix = current_path[len(normalized_path) :]
            self.client.query(
                "UPDATE asset_groups SET path = ? WHERE path = ?",
                [f"{temp_prefix}{suffix}", current_path],
            )

        staged_rows = self.client.query_rows(
            """
            SELECT path
            FROM asset_groups
            WHERE path = ? OR path LIKE ?
            ORDER BY length(path) ASC, path COLLATE NOCASE ASC
            """,
            [temp_prefix, f"{temp_prefix}/%"],
        )
        for row in staged_rows:
            current_path = row["path"]
            suffix = current_path[len(temp_prefix) :]
            self.client.query(
                "UPDATE asset_groups SET path = ? WHERE path = ?",
                [f"{target_path}{suffix}", current_path],
            )

        asset_rows = self.client.query_rows(
            """
            SELECT id, category
            FROM assets
            WHERE category = ? OR category LIKE ?
            """,
            [normalized_path, f"{normalized_path}/%"],
        )
        for row in asset_rows:
            current_category = normalize_asset_group_path(row["category"])
            suffix = current_category[len(normalized_path) :]
            self.client.query(
                """
                UPDATE assets
                SET category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [f"{target_path}{suffix}", row["id"]],
            )

        _shadow_rename_asset_group(normalized_path, normalized_name)
        _cache_invalidate("assets:")
        return target_path

    def delete_asset_group(self, path: str):
        normalized = normalize_asset_group_path(path)
        if not normalized:
            raise AssetGroupError("삭제할 폴더를 선택해주세요.")
        asset_row = self.client.query_first(
            """
            SELECT COUNT(*) AS count
            FROM assets
            WHERE category = ? OR category LIKE ?
            """,
            [normalized, f"{normalized}/%"],
        )
        if int(asset_row["count"] or 0):
            raise AssetGroupError("하위 Asset이 남아 있는 폴더는 삭제할 수 없습니다.")

        self.client.query(
            "DELETE FROM asset_groups WHERE path = ? OR path LIKE ?",
            [normalized, f"{normalized}/%"],
        )
        _shadow_delete_asset_group(normalized)
        _cache_invalidate("assets:")

    def create_asset(self, data):
        data["category"] = self.create_asset_group(data["category"])
        result = self.client.query(
            """
            INSERT INTO assets (
                title, asset_type, category, file_name, original_filename, object_key, url,
                content_type, size, checksum, status, is_hidden, created_by, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            [
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
            ],
        )
        asset_id = result.get("meta", {}).get("last_row_id")
        if asset_id is None:
            raise D1RepositoryError("Failed to create asset in D1.")
        _shadow_upsert_asset(asset_id, data)
        sync_asset_tags_local(get_db(), asset_id, data["tags"])
        for tag in [tag.strip() for tag in (data["tags"] or "").split(",") if tag.strip()]:
            self.client.query("INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)", [asset_id, tag])
        _cache_invalidate("assets:")
        return asset_id

    def update_asset(self, asset_id: int, data):
        data["category"] = self.create_asset_group(data["category"])
        self.client.query(
            """
            UPDATE assets
            SET title = ?, asset_type = ?, category = ?, file_name = ?, original_filename = ?,
                object_key = ?, url = ?, content_type = ?, size = ?, checksum = ?,
                status = ?, is_hidden = ?, created_by = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [
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
            ],
        )
        self.client.query("DELETE FROM asset_tags WHERE asset_id = ?", [asset_id])
        for tag in [tag.strip() for tag in (data["tags"] or "").split(",") if tag.strip()]:
            self.client.query("INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)", [asset_id, tag])
        _shadow_upsert_asset(asset_id, data)
        sync_asset_tags_local(get_db(), asset_id, data["tags"])
        _cache_invalidate("assets:")

    def delete_asset(self, asset_id: int):
        self.client.query("DELETE FROM asset_tags WHERE asset_id = ?", [asset_id])
        self.client.query("DELETE FROM assets WHERE id = ?", [asset_id])
        _shadow_delete_asset(asset_id)
        _cache_invalidate("assets:")


@dataclass
class D1WbsRepository:
    client: D1RestClient

    def fetch_task_with_links(self, task_id: int):
        task = self.client.query_first(
            """
            SELECT t.*, m.name AS assignee_name, p.title AS parent_title
            FROM wbs_tasks t
            LEFT JOIN members m ON m.id = t.assignee_id
            LEFT JOIN wbs_tasks p ON p.id = t.parent_id
            WHERE t.id = ?
            """,
            [task_id],
        )
        if not task:
            return None, []

        rows = self.client.query_rows(
            "SELECT document_id FROM task_documents WHERE task_id = ? ORDER BY document_id ASC",
            [task_id],
        )
        return task, [row["document_id"] for row in rows]

    def fetch_tasks_for_filters(self, filters: dict[str, str]):
        clauses = []
        params: list[Any] = []
        if filters.get("status"):
            clauses.append("t.status = ?")
            params.append(filters["status"])
        if filters.get("assignee_id"):
            clauses.append("t.assignee_id = ?")
            params.append(int(filters["assignee_id"]))
        if filters.get("priority"):
            clauses.append("t.priority = ?")
            params.append(filters["priority"])
        if filters.get("platform"):
            clauses.append("COALESCE(t.platform, 'Agentic Product Studio') = ?")
            params.append(filters["platform"])
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return self.client.query_rows(
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
        )

    def create_task(self, data):
        result = self.client.query(
            """
            INSERT INTO wbs_tasks (
                parent_id, title, description, assignee_id, platform, status, priority,
                start_date, due_date, completed_date, progress, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            [
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
            ],
        )
        task_id = result.get("meta", {}).get("last_row_id")
        if task_id is None:
            raise D1RepositoryError("Failed to create WBS task in D1.")
        _shadow_upsert_wbs_task(task_id, data)
        _cache_invalidate("common:task_link_options", "common:parent_task_options", "dashboard:", "members:")
        return task_id

    def sync_task_documents(self, task_id: int, document_ids: list[int]):
        self.client.query("DELETE FROM task_documents WHERE task_id = ?", [task_id])
        for document_id in sorted(set(document_ids)):
            self.client.query(
                "INSERT OR IGNORE INTO task_documents (task_id, document_id) VALUES (?, ?)",
                [task_id, document_id],
            )
        sync_task_documents_for_task_local(get_db(), task_id, document_ids)
        _cache_invalidate("dashboard:")

    def update_task(self, task_id: int, data):
        self.client.query(
            """
            UPDATE wbs_tasks
            SET parent_id = ?, title = ?, description = ?, assignee_id = ?, platform = ?,
                status = ?, priority = ?, start_date = ?, due_date = ?,
                completed_date = ?, progress = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [
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
            ],
        )
        _shadow_upsert_wbs_task(task_id, data)
        _cache_invalidate("common:task_link_options", "common:parent_task_options", "dashboard:", "members:")

    def delete_task(self, task_id: int):
        self.client.query("DELETE FROM task_documents WHERE task_id = ?", [task_id])
        self.client.query(
            "UPDATE schedules SET wbs_task_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE wbs_task_id = ?",
            [task_id],
        )
        self.client.query("UPDATE wbs_tasks SET parent_id = NULL WHERE parent_id = ?", [task_id])
        self.client.query("DELETE FROM wbs_tasks WHERE id = ?", [task_id])
        _shadow_delete_wbs_task(task_id)
        _cache_invalidate("common:task_link_options", "common:parent_task_options", "dashboard:", "members:")


@dataclass
class D1MembersRepository:
    client: D1RestClient

    def fetch_member(self, member_id: int):
        return self.client.query_first("SELECT * FROM members WHERE id = ?", [member_id])

    def list_members(self):
        cache_key = "members:list"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
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
            ),
        )

    def create_member(self, data):
        result = self.client.query(
            """
            INSERT INTO members (name, role, part, contact, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            [data["name"], data["role"], data["part"], data["contact"], data["is_active"]],
        )
        member_id = result.get("meta", {}).get("last_row_id")
        if member_id is None:
            raise D1RepositoryError("Failed to create member in D1.")
        _shadow_upsert_member(member_id, data)
        _cache_invalidate("members:", "common:active_members", "dashboard:")
        return member_id

    def update_member(self, member_id: int, data):
        self.client.query(
            """
            UPDATE members
            SET name = ?, role = ?, part = ?, contact = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [data["name"], data["role"], data["part"], data["contact"], data["is_active"], member_id],
        )
        _shadow_upsert_member(member_id, data)
        _cache_invalidate("members:", "common:active_members", "dashboard:")

    def delete_member(self, member_id: int):
        self.client.query(
            "UPDATE wbs_tasks SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
            [member_id],
        )
        self.client.query(
            "UPDATE schedules SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?",
            [member_id],
        )
        self.client.query(
            "UPDATE documents SET author_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE author_id = ?",
            [member_id],
        )
        self.client.query("DELETE FROM members WHERE id = ?", [member_id])
        _shadow_delete_member(member_id)
        _cache_invalidate("members:", "common:active_members", "dashboard:")


@dataclass
class D1SchedulesRepository:
    client: D1RestClient

    def fetch_schedule(self, schedule_id: int):
        return self.client.query_first(
            """
            SELECT s.*, m.name AS assignee_name, t.title AS task_title
            FROM schedules s
            LEFT JOIN members m ON m.id = s.assignee_id
            LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
            WHERE s.id = ?
            """,
            [schedule_id],
        )

    def list_schedules(self):
        cache_key = "schedules:list"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT s.*, m.name AS assignee_name, t.title AS task_title
            FROM schedules s
            LEFT JOIN members m ON m.id = s.assignee_id
            LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
            ORDER BY s.start_date ASC, s.end_date ASC, s.id ASC
            """
            ),
        )

    def create_schedule(self, data):
        result = self.client.query(
            """
            INSERT INTO schedules (
                title, description, start_date, end_date, assignee_id, wbs_task_id, schedule_type, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            [
                data["title"],
                data["description"],
                data["start_date"],
                data["end_date"],
                data["assignee_id"],
                data["wbs_task_id"],
                data["schedule_type"],
            ],
        )
        schedule_id = result.get("meta", {}).get("last_row_id")
        if schedule_id is None:
            raise D1RepositoryError("Failed to create schedule in D1.")
        _shadow_upsert_schedule(schedule_id, data)
        _cache_invalidate("schedules:", "dashboard:", "members:")
        return schedule_id

    def update_schedule(self, schedule_id: int, data):
        self.client.query(
            """
            UPDATE schedules
            SET title = ?, description = ?, start_date = ?, end_date = ?,
                assignee_id = ?, wbs_task_id = ?, schedule_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [
                data["title"],
                data["description"],
                data["start_date"],
                data["end_date"],
                data["assignee_id"],
                data["wbs_task_id"],
                data["schedule_type"],
                schedule_id,
            ],
        )
        _shadow_upsert_schedule(schedule_id, data)
        _cache_invalidate("schedules:", "dashboard:", "members:")

    def delete_schedule(self, schedule_id: int):
        self.client.query("DELETE FROM schedules WHERE id = ?", [schedule_id])
        _shadow_delete_schedule(schedule_id)
        _cache_invalidate("schedules:", "dashboard:", "members:")


@dataclass
class D1DashboardRepository:
    client: D1RestClient

    def fetch_dashboard_summary(self, today_str: str):
        cache_key = f"dashboard:summary:{today_str}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_first(
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
            [today_str],
            ),
        )

    def fetch_week_due_tasks(self, today_str: str, week_end_str: str):
        cache_key = f"dashboard:week_due:{today_str}:{week_end_str}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT t.id, t.title, t.status, t.priority, t.due_date, m.name AS assignee_name
            FROM wbs_tasks t
            LEFT JOIN members m ON m.id = t.assignee_id
            WHERE t.due_date BETWEEN ? AND ?
              AND t.status != '완료'
            ORDER BY t.due_date ASC, t.id ASC
            LIMIT 8
            """,
            [today_str, week_end_str],
            ),
        )

    def fetch_recent_documents(self):
        cache_key = "dashboard:recent_documents"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT d.id, d.title, d.doc_type, d.updated_at, m.name AS author_name
            FROM documents d
            LEFT JOIN members m ON m.id = d.author_id
            WHERE COALESCE(d.is_hidden, 0) = 0
            ORDER BY d.updated_at DESC, d.id DESC
            LIMIT 6
            """
            ),
        )

    def fetch_recent_tasks(self):
        cache_key = "dashboard:recent_tasks"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
            """
            SELECT t.id, t.title, t.status, t.priority, t.updated_at, m.name AS assignee_name
            FROM wbs_tasks t
            LEFT JOIN members m ON m.id = t.assignee_id
            ORDER BY t.updated_at DESC, t.id DESC
            LIMIT 6
            """
            ),
        )

    def fetch_pinned_notice(self):
        cache_key = "dashboard:pinned_notice"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_first(
            """
            SELECT id, title, content, updated_at
            FROM notices
            WHERE is_pinned = 1
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """
            ),
        )

    def fetch_upcoming_schedules(self, today_str: str):
        cache_key = f"dashboard:upcoming_schedules:{today_str}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        return _cache_set(
            cache_key,
            self.client.query_rows(
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
            [today_str],
            ),
        )


def build_d1_provider():
    config = current_app.config
    client = D1RestClient(
        account_id=config.get("CLOUDFLARE_ACCOUNT_ID", ""),
        database_id=config.get("D1_DATABASE_ID", ""),
        api_token=config.get("CLOUDFLARE_API_TOKEN", ""),
    )
    return RepositoryProvider(
        common=D1CommonRepository(client),
        documents=D1DocumentsRepository(client),
        assets=D1AssetsRepository(client),
        wbs=D1WbsRepository(client),
        members=D1MembersRepository(client),
        schedules=D1SchedulesRepository(client),
        dashboard=D1DashboardRepository(client),
    )
