from __future__ import annotations

from ..db import get_db


def get_repository_db():
    return get_db()
