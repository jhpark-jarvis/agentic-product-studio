from __future__ import annotations

from dataclasses import dataclass

from flask import current_app, g

from .contracts import (
    AssetsRepository,
    CommonRepository,
    DashboardRepository,
    DocumentsRepository,
    MembersRepository,
    SchedulesRepository,
    WbsRepository,
)


@dataclass
class RepositoryProvider:
    common: CommonRepository
    documents: DocumentsRepository
    assets: AssetsRepository
    wbs: WbsRepository
    members: MembersRepository
    schedules: SchedulesRepository
    dashboard: DashboardRepository


def _build_provider():
    backend = current_app.config.get("REPOSITORY_BACKEND", "sqlite")
    if backend == "sqlite":
        from .sqlite_backend import build_sqlite_provider

        return build_sqlite_provider()
    if backend == "d1":
        from .d1_backend import build_d1_provider

        return build_d1_provider()
    raise RuntimeError(f"Unsupported repository backend: {backend}")


def get_repository_provider() -> RepositoryProvider:
    if "repository_provider" not in g:
        g.repository_provider = _build_provider()
    return g.repository_provider
