from __future__ import annotations

from dataclasses import dataclass

from . import common as common_queries
from . import dashboard as dashboard_queries
from . import documents as document_queries
from . import members as member_queries
from . import schedules as schedule_queries
from . import wbs as wbs_queries
from ..db import (
    assign_draft_assets_to_document,
    create_document_asset,
    delete_document_asset,
    ensure_document_folder,
    fetch_document_asset,
    fetch_document_assets,
    sync_document_tags,
    sync_task_documents,
    sync_task_documents_for_document,
)
from .provider import RepositoryProvider


@dataclass
class SQLiteCommonRepository:
    db: object

    def fetch_active_members(self):
        return common_queries.fetch_active_members(self.db)

    def fetch_document_link_options(self):
        return common_queries.fetch_document_link_options(self.db)

    def fetch_task_link_options(self):
        return common_queries.fetch_task_link_options(self.db)

    def fetch_parent_task_options(self, exclude_task_id: int | None = None):
        return common_queries.fetch_parent_task_options(self.db, exclude_task_id)


@dataclass
class SQLiteDocumentsRepository:
    db: object

    def fetch_document_folders(self, doc_type: str | None = None):
        return document_queries.fetch_document_folders(self.db, doc_type)

    def fetch_folder(self, folder_id: int):
        return document_queries.fetch_folder(self.db, folder_id)

    def ensure_folder(self, doc_type: str, folder_name: str):
        return ensure_document_folder(self.db, doc_type, folder_name)

    def fetch_document_with_relations(self, document_id: int):
        return document_queries.fetch_document_with_relations(self.db, document_id)

    def list_documents(self, *, search: str, doc_type: str, tag: str, folder_id: str, limit: int, offset: int):
        return document_queries.list_documents(
            self.db,
            search=search,
            doc_type=doc_type,
            tag=tag,
            folder_id=folder_id,
            limit=limit,
            offset=offset,
        )

    def fetch_tag_options(self):
        return document_queries.fetch_tag_options(self.db)

    def create_document(self, data, folder_id):
        return document_queries.create_document(self.db, data, folder_id)

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
        return create_document_asset(
            self.db,
            document_id=document_id,
            draft_key=draft_key,
            object_key=object_key,
            url=url,
            original_filename=original_filename,
            content_type=content_type,
            size=size,
        )

    def fetch_document_assets(self, document_id: int):
        return fetch_document_assets(self.db, document_id)

    def fetch_document_asset(self, asset_id: int):
        return fetch_document_asset(self.db, asset_id)

    def delete_document_asset(self, asset_id: int):
        delete_document_asset(self.db, asset_id)

    def assign_draft_assets(self, document_id: int, draft_key: str):
        assign_draft_assets_to_document(self.db, document_id, draft_key)

    def sync_document_tags(self, document_id: int, tags_text: str):
        sync_document_tags(self.db, document_id, tags_text)

    def sync_task_documents(self, document_id: int, task_ids: list[int]):
        sync_task_documents_for_document(self.db, document_id, task_ids)

    def update_document(self, document_id, data, folder_id):
        return document_queries.update_document(self.db, document_id, data, folder_id)

    def delete_document(self, document_id):
        return document_queries.delete_document(self.db, document_id)

    def update_document_folder(self, document_id, doc_type, folder_id):
        return document_queries.update_document_folder(self.db, document_id, doc_type, folder_id)


@dataclass
class SQLiteWbsRepository:
    db: object

    def fetch_task_with_links(self, task_id: int):
        return wbs_queries.fetch_task_with_links(self.db, task_id)

    def fetch_tasks_for_filters(self, filters: dict[str, str]):
        return wbs_queries.fetch_tasks_for_filters(self.db, filters)

    def create_task(self, data):
        return wbs_queries.create_task(self.db, data)

    def sync_task_documents(self, task_id: int, document_ids: list[int]):
        sync_task_documents(self.db, task_id, document_ids)

    def update_task(self, task_id: int, data):
        return wbs_queries.update_task(self.db, task_id, data)

    def delete_task(self, task_id: int):
        return wbs_queries.delete_task(self.db, task_id)


@dataclass
class SQLiteMembersRepository:
    db: object

    def fetch_member(self, member_id: int):
        return member_queries.fetch_member(self.db, member_id)

    def list_members(self):
        return member_queries.list_members(self.db)

    def create_member(self, data):
        return member_queries.create_member(self.db, data)

    def update_member(self, member_id: int, data):
        return member_queries.update_member(self.db, member_id, data)

    def delete_member(self, member_id: int):
        return member_queries.delete_member(self.db, member_id)


@dataclass
class SQLiteSchedulesRepository:
    db: object

    def fetch_schedule(self, schedule_id: int):
        return schedule_queries.fetch_schedule(self.db, schedule_id)

    def list_schedules(self):
        return schedule_queries.list_schedules(self.db)

    def create_schedule(self, data):
        return schedule_queries.create_schedule(self.db, data)

    def update_schedule(self, schedule_id: int, data):
        return schedule_queries.update_schedule(self.db, schedule_id, data)

    def delete_schedule(self, schedule_id: int):
        return schedule_queries.delete_schedule(self.db, schedule_id)


@dataclass
class SQLiteDashboardRepository:
    db: object

    def fetch_dashboard_summary(self, today_str: str):
        return dashboard_queries.fetch_dashboard_summary(self.db, today_str)

    def fetch_week_due_tasks(self, today_str: str, week_end_str: str):
        return dashboard_queries.fetch_week_due_tasks(self.db, today_str, week_end_str)

    def fetch_recent_documents(self):
        return dashboard_queries.fetch_recent_documents(self.db)

    def fetch_recent_tasks(self):
        return dashboard_queries.fetch_recent_tasks(self.db)

    def fetch_pinned_notice(self):
        return dashboard_queries.fetch_pinned_notice(self.db)

    def fetch_upcoming_schedules(self, today_str: str):
        return dashboard_queries.fetch_upcoming_schedules(self.db, today_str)


def build_sqlite_provider():
    from .db_access import get_repository_db

    db = get_repository_db()
    return RepositoryProvider(
        common=SQLiteCommonRepository(db),
        documents=SQLiteDocumentsRepository(db),
        wbs=SQLiteWbsRepository(db),
        members=SQLiteMembersRepository(db),
        schedules=SQLiteSchedulesRepository(db),
        dashboard=SQLiteDashboardRepository(db),
    )
