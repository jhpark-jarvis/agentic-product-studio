from __future__ import annotations

import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

from flask import Flask


PAGE_VIEW_LOGGER_NAME = "page_views"


def _build_page_view_logger(logs_dir: Path) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "page-views.log"

    logger = logging.getLogger(PAGE_VIEW_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    resolved_log_path = log_path.resolve()
    for existing_handler in logger.handlers:
        if getattr(existing_handler, "baseFilename", None) == str(resolved_log_path):
            return logger

    handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def setup_page_view_logger(app: Flask) -> None:
    logger = _build_page_view_logger(Path(app.instance_path) / "logs")
    app.extensions["page_view_logger"] = logger


def setup_page_view_logger_for_path(instance_path: str | Path) -> logging.Logger:
    return _build_page_view_logger(Path(instance_path) / "logs")


def write_page_view_log(app: Flask, payload: dict) -> None:
    logger = app.extensions.get("page_view_logger")
    if logger is None:
        setup_page_view_logger(app)
        logger = app.extensions.get("page_view_logger")

    logger.info(json.dumps(payload, ensure_ascii=False))


def write_page_view_log_with_logger(logger: logging.Logger, payload: dict) -> None:
    logger.info(json.dumps(payload, ensure_ascii=False))


def _log_dir(app: Flask) -> Path:
    return Path(app.instance_path) / "logs"


def _log_dir_for_path(instance_path: str | Path) -> Path:
    return Path(instance_path) / "logs"


def iter_page_view_log_files(app: Flask) -> list[Path]:
    log_dir = _log_dir(app)
    if not log_dir.exists():
        return []
    return sorted(
        log_dir.glob("page-views.log*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def iter_page_view_log_files_for_path(instance_path: str | Path) -> list[Path]:
    log_dir = _log_dir_for_path(instance_path)
    if not log_dir.exists():
        return []
    return sorted(
        log_dir.glob("page-views.log*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def read_page_view_logs(
    app: Flask,
    *,
    limit: int = 200,
    search: str = "",
    visitor_id: str = "",
) -> list[dict[str, Any]]:
    normalized_search = (search or "").strip().lower()
    normalized_visitor_id = (visitor_id or "").strip()
    rows: list[dict[str, Any]] = []

    for log_file in iter_page_view_log_files(app):
        try:
            lines = log_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        for raw_line in reversed(lines):
            if not raw_line.strip():
                continue
            try:
                item = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            if normalized_visitor_id and item.get("visitor_id") != normalized_visitor_id:
                continue

            if normalized_search:
                haystack = " ".join(
                    [
                        str(item.get("path") or ""),
                        str(item.get("referrer") or ""),
                        str(item.get("visitor_id") or ""),
                        str(item.get("session_id") or ""),
                        str(item.get("ip") or ""),
                        str(item.get("user_agent") or ""),
                    ]
                ).lower()
                if normalized_search not in haystack:
                    continue

            rows.append(item)
            if len(rows) >= limit:
                return rows

    return rows


def read_page_view_logs_for_path(
    instance_path: str | Path,
    *,
    limit: int = 200,
    search: str = "",
    visitor_id: str = "",
) -> list[dict[str, Any]]:
    normalized_search = (search or "").strip().lower()
    normalized_visitor_id = (visitor_id or "").strip()
    rows: list[dict[str, Any]] = []

    for log_file in iter_page_view_log_files_for_path(instance_path):
        try:
            lines = log_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        for raw_line in reversed(lines):
            if not raw_line.strip():
                continue
            try:
                item = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            if normalized_visitor_id and item.get("visitor_id") != normalized_visitor_id:
                continue

            if normalized_search:
                haystack = " ".join(
                    [
                        str(item.get("path") or ""),
                        str(item.get("referrer") or ""),
                        str(item.get("visitor_id") or ""),
                        str(item.get("session_id") or ""),
                        str(item.get("ip") or ""),
                        str(item.get("user_agent") or ""),
                    ]
                ).lower()
                if normalized_search not in haystack:
                    continue

            rows.append(item)
            if len(rows) >= limit:
                return rows

    return rows
