from __future__ import annotations

from fastapi import HTTPException, Request


def get_settings(request: Request):
    return request.app.state.settings


def get_repository_provider(request: Request):
    provider = getattr(request.app.state, "repository_provider", None)
    if provider is None:
        raise HTTPException(status_code=503, detail="Repository provider is not initialized.")
    return provider


def get_runtime_sqlite_db(request: Request):
    return getattr(request.app.state, "sqlite_db", None)
