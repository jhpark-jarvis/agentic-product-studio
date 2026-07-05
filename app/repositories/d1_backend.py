from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app

from .provider import RepositoryProvider


class D1RepositoryError(RuntimeError):
    pass


class D1WriteNotSupportedError(NotImplementedError):
    pass


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


@dataclass
class D1CommonRepository:
    client: D1RestClient

    def fetch_active_members(self):
        return self.client.query_rows(
            """
            SELECT id, name, role, part
            FROM members
            WHERE is_active = 1
            ORDER BY name COLLATE NOCASE ASC
            """
        )

    def fetch_document_link_options(self):
        return self.client.query_rows(
            """
            SELECT id, title, doc_type, is_hidden
            FROM documents
            ORDER BY is_hidden ASC, updated_at DESC, title COLLATE NOCASE ASC
            """
        )

    def fetch_task_link_options(self):
        return self.client.query_rows(
            """
            SELECT id, title, status
            FROM wbs_tasks
            ORDER BY updated_at DESC, id DESC
            """
        )

    def fetch_parent_task_options(self, exclude_task_id: int | None = None):
        if exclude_task_id is None:
            return self.client.query_rows(
                "SELECT id, title FROM wbs_tasks ORDER BY created_at ASC, id ASC"
            )
        return self.client.query_rows(
            """
            SELECT id, title
            FROM wbs_tasks
            WHERE id != ?
            ORDER BY created_at ASC, id ASC
            """,
            [exclude_task_id],
        )


@dataclass
class D1DocumentsRepository:
    client: D1RestClient

    def fetch_document_folders(self, doc_type: str | None = None):
        if doc_type:
            return self.client.query_rows(
                """
                SELECT id, doc_type, name
                FROM document_folders
                WHERE doc_type = ?
                ORDER BY name COLLATE NOCASE ASC
                """,
                [doc_type],
            )
        return self.client.query_rows(
            """
            SELECT id, doc_type, name
            FROM document_folders
            ORDER BY doc_type COLLATE NOCASE ASC, name COLLATE NOCASE ASC
            """
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

    def fetch_document_with_relations(self, document_id: int):
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
        return document, related_tasks, [row["tag"] for row in tag_rows]

    def list_documents(
        self, *, search: str, doc_type: str, tag: str, folder_id: str, limit: int, offset: int
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
        if folder_id and folder_id.isdigit():
            clauses.append("d.folder_id = ?")
            params.append(int(folder_id))

        where_sql = f"WHERE {' AND '.join(clauses)}"
        total_count_row = self.client.query_first(
            f"""
            SELECT COUNT(DISTINCT d.id) AS count
            FROM documents d
            {' '.join(joins)}
            {where_sql}
            """,
            params,
        )
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
        return self.client.query_rows(
            """
            SELECT tag, COUNT(*) AS usage_count
            FROM document_tags
            GROUP BY tag
            ORDER BY tag COLLATE NOCASE ASC
            """
        )

    def create_document(self, data, folder_id):
        _raise_write_not_supported()

    def update_document(self, document_id, data, folder_id):
        _raise_write_not_supported()

    def delete_document(self, document_id):
        _raise_write_not_supported()

    def update_document_folder(self, document_id, doc_type, folder_id):
        _raise_write_not_supported()


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
        _raise_write_not_supported()

    def update_task(self, task_id: int, data):
        _raise_write_not_supported()

    def delete_task(self, task_id: int):
        _raise_write_not_supported()


@dataclass
class D1MembersRepository:
    client: D1RestClient

    def fetch_member(self, member_id: int):
        return self.client.query_first("SELECT * FROM members WHERE id = ?", [member_id])

    def list_members(self):
        return self.client.query_rows(
            """
            SELECT
                m.*,
                (SELECT COUNT(*) FROM wbs_tasks t WHERE t.assignee_id = m.id) AS task_count,
                (SELECT COUNT(*) FROM schedules s WHERE s.assignee_id = m.id) AS schedule_count
            FROM members m
            ORDER BY m.is_active DESC, m.name COLLATE NOCASE ASC
            """
        )

    def create_member(self, data):
        _raise_write_not_supported()

    def update_member(self, member_id: int, data):
        _raise_write_not_supported()

    def delete_member(self, member_id: int):
        _raise_write_not_supported()


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
        return self.client.query_rows(
            """
            SELECT s.*, m.name AS assignee_name, t.title AS task_title
            FROM schedules s
            LEFT JOIN members m ON m.id = s.assignee_id
            LEFT JOIN wbs_tasks t ON t.id = s.wbs_task_id
            ORDER BY s.start_date ASC, s.end_date ASC, s.id ASC
            """
        )

    def create_schedule(self, data):
        _raise_write_not_supported()

    def update_schedule(self, schedule_id: int, data):
        _raise_write_not_supported()

    def delete_schedule(self, schedule_id: int):
        _raise_write_not_supported()


@dataclass
class D1DashboardRepository:
    client: D1RestClient

    def fetch_dashboard_summary(self, today_str: str):
        return self.client.query_first(
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
        )

    def fetch_week_due_tasks(self, today_str: str, week_end_str: str):
        return self.client.query_rows(
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
        )

    def fetch_recent_documents(self):
        return self.client.query_rows(
            """
            SELECT d.id, d.title, d.doc_type, d.updated_at, m.name AS author_name
            FROM documents d
            LEFT JOIN members m ON m.id = d.author_id
            WHERE COALESCE(d.is_hidden, 0) = 0
            ORDER BY d.updated_at DESC, d.id DESC
            LIMIT 6
            """
        )

    def fetch_recent_tasks(self):
        return self.client.query_rows(
            """
            SELECT t.id, t.title, t.status, t.priority, t.updated_at, m.name AS assignee_name
            FROM wbs_tasks t
            LEFT JOIN members m ON m.id = t.assignee_id
            ORDER BY t.updated_at DESC, t.id DESC
            LIMIT 6
            """
        )

    def fetch_pinned_notice(self):
        return self.client.query_first(
            """
            SELECT id, title, content, updated_at
            FROM notices
            WHERE is_pinned = 1
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """
        )

    def fetch_upcoming_schedules(self, today_str: str):
        return self.client.query_rows(
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
        wbs=D1WbsRepository(client),
        members=D1MembersRepository(client),
        schedules=D1SchedulesRepository(client),
        dashboard=D1DashboardRepository(client),
    )
