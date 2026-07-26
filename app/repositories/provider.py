from __future__ import annotations

from dataclasses import dataclass

from flask import current_app, g

from ..db import get_db
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
    from .runtime_provider import build_repository_provider

    config = dict(current_app.config)
    if config.get("REPOSITORY_BACKEND", "sqlite") == "sqlite":
        return build_repository_provider(config, db=get_db())
    return build_repository_provider(config)


def get_repository_provider() -> RepositoryProvider:
    if "repository_provider" not in g:
        g.repository_provider = _build_provider()
    return g.repository_provider
