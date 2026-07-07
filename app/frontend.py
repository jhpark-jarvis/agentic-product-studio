from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, current_app, send_from_directory


bp = Blueprint("frontend", __name__)


def _frontend_dir() -> Path:
    return Path(current_app.static_folder) / "frontend"


def _send_frontend_index():
    frontend_dir = _frontend_dir()
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        abort(404, description="React frontend build not found. Run the frontend build first.")
    return send_from_directory(frontend_dir, "index.html")


@bp.route("/app")
@bp.route("/app/")
def app_index():
    return _send_frontend_index()


@bp.route("/app/<path:path>")
def app_routes(path: str):
    frontend_dir = _frontend_dir()
    target_path = frontend_dir / path
    if target_path.exists() and target_path.is_file():
        return send_from_directory(frontend_dir, path)
    return _send_frontend_index()
