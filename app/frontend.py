from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, current_app, redirect, send_from_directory


bp = Blueprint("frontend", __name__)


def _frontend_dir() -> Path:
    return Path(current_app.static_folder) / "frontend"


def _send_frontend_index():
    frontend_dir = _frontend_dir()
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        abort(404, description="React frontend build not found. Run the frontend build first.")
    response = send_from_directory(frontend_dir, "index.html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def _upload_dir() -> Path:
    return Path(current_app.config["UPLOAD_FOLDER"])


def _normalize_legacy_path(path: str) -> str:
    normalized = path or ""
    full_path = f"/app/{normalized}".rstrip("/")
    if not full_path:
        return "/"
    return (
        full_path.replace("/app/documents", "/documents", 1)
        .replace("/app/wbs", "/wbs", 1)
        .replace("/app/schedules", "/schedules", 1)
        .replace("/app/members", "/members", 1)
        .replace("/app/dashboard", "/", 1)
        .replace("/app", "/", 1)
    )


def _normalize_short_path(segment: str, path: str | None = None) -> str:
    suffix = f"/{path}" if path else ""
    return {
        "document": f"/documents{suffix}",
        "asset": f"/assets{suffix}",
        "task": f"/wbs{suffix}",
        "schedule": f"/schedules{suffix}",
        "member": f"/members{suffix}",
    }[segment]


@bp.route("/")
@bp.route("/dashboard")
@bp.route("/documents")
@bp.route("/documents/")
@bp.route("/documents/<path:path>")
@bp.route("/assets")
@bp.route("/assets/")
@bp.route("/assets/<path:path>")
@bp.route("/wbs")
@bp.route("/wbs/")
@bp.route("/wbs/<path:path>")
@bp.route("/schedules")
@bp.route("/schedules/")
@bp.route("/schedules/<path:path>")
@bp.route("/members")
@bp.route("/members/")
@bp.route("/members/<path:path>")
@bp.route("/log")
@bp.route("/log/")
def app_index(path: str | None = None):
    return _send_frontend_index()


@bp.route("/app")
@bp.route("/app/")
def legacy_app_index():
    return redirect("/", code=302)


@bp.route("/app/<path:path>")
def app_routes(path: str):
    return redirect(_normalize_legacy_path(path), code=302)


@bp.route("/document")
@bp.route("/document/")
@bp.route("/document/<path:path>")
def legacy_document_routes(path: str | None = None):
    return redirect(_normalize_short_path("document", path), code=302)


@bp.route("/asset")
@bp.route("/asset/")
@bp.route("/asset/<path:path>")
def legacy_asset_routes(path: str | None = None):
    return redirect(_normalize_short_path("asset", path), code=302)


@bp.route("/task")
@bp.route("/task/")
@bp.route("/task/<path:path>")
def legacy_task_routes(path: str | None = None):
    return redirect(_normalize_short_path("task", path), code=302)


@bp.route("/schedule")
@bp.route("/schedule/")
@bp.route("/schedule/<path:path>")
def legacy_schedule_routes(path: str | None = None):
    return redirect(_normalize_short_path("schedule", path), code=302)


@bp.route("/member")
@bp.route("/member/")
@bp.route("/member/<path:path>")
def legacy_member_routes(path: str | None = None):
    return redirect(_normalize_short_path("member", path), code=302)


@bp.route("/logs")
@bp.route("/logs/")
def legacy_logs_route():
    return redirect("/log", code=302)


@bp.route("/uploads/<path:path>")
def uploaded_files(path: str):
    return send_from_directory(_upload_dir(), path)
