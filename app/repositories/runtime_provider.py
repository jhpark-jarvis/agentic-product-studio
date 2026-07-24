from __future__ import annotations

from .d1_backend import build_d1_provider_from_config
from .sqlite_backend import build_sqlite_provider_for_db


def build_repository_provider(config: dict[str, object], *, db=None):
    backend = config.get("REPOSITORY_BACKEND", "sqlite")
    if backend == "sqlite":
        if db is None:
            raise RuntimeError("SQLite repository backend requires a database connection.")
        return build_sqlite_provider_for_db(db)
    if backend == "d1":
        return build_d1_provider_from_config(config)
    raise RuntimeError(f"Unsupported repository backend: {backend}")
