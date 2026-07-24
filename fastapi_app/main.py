from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import (
    clear_runtime_db_connection,
    connect_sqlite_database,
    initialize_sqlite_database,
    set_runtime_db_connection,
)
from app.repositories.runtime_provider import build_repository_provider
from app.settings import AppSettings, load_settings

from .routers.assets import router as assets_router
from .routers.dashboard import router as dashboard_router
from .routers.documents import public_router as document_public_router
from .routers.documents import router as documents_router
from .routers.frontend import router as frontend_router
from .routers.members import router as members_router
from .routers.schedules import router as schedules_router
from .routers.system import router as system_router
from .routers.telemetry import router as telemetry_router
from .routers.wbs import router as wbs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: AppSettings = app.state.settings
    config = settings.to_config_mapping()

    initialize_sqlite_database(settings.database)
    db = connect_sqlite_database(settings.database)
    app.state.sqlite_db = db
    set_runtime_db_connection(db)

    if settings.repository_backend == "sqlite":
        app.state.repository_provider = build_repository_provider(config, db=db)
    else:
        app.state.repository_provider = build_repository_provider(config)

    try:
        yield
    finally:
        clear_runtime_db_connection()
        db = getattr(app.state, "sqlite_db", None)
        if db is not None:
            db.close()
            app.state.sqlite_db = None


def create_app(settings: AppSettings | None = None) -> FastAPI:
    resolved_settings = settings or load_settings()
    app = FastAPI(
        title="Personal Service FastAPI",
        version="0.1.0-fastapi",
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.mount(
        "/static",
        StaticFiles(directory=Path(resolved_settings.project_root) / "app" / "static"),
        name="static",
    )
    app.mount(
        "/uploads",
        StaticFiles(directory=resolved_settings.upload_folder),
        name="uploads",
    )
    app.include_router(system_router)
    app.include_router(dashboard_router)
    app.include_router(documents_router)
    app.include_router(document_public_router)
    app.include_router(assets_router)
    app.include_router(wbs_router)
    app.include_router(schedules_router)
    app.include_router(members_router)
    app.include_router(telemetry_router)
    app.include_router(frontend_router)
    return app


app = create_app()
