from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


TABLE_EXPORT_ORDER = [
    "members",
    "document_folders",
    "documents",
    "document_tags",
    "wbs_tasks",
    "task_documents",
    "schedules",
    "notices",
    "assets",
    "document_assets",
]


def quote_sqlite_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def ordered_select_sql(connection: sqlite3.Connection, table_name: str) -> str:
    columns = [
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    ]
    if "id" in columns:
        return f"SELECT * FROM {table_name} ORDER BY id"
    if {"task_id", "document_id"}.issubset(columns):
        return f"SELECT * FROM {table_name} ORDER BY task_id, document_id"
    if "document_id" in columns:
        return f"SELECT * FROM {table_name} ORDER BY document_id, id"
    return f"SELECT * FROM {table_name}"


def export_table(connection: sqlite3.Connection, table_name: str) -> list[str]:
    if not table_exists(connection, table_name):
        return [f"-- Skipped missing table: {table_name}"]

    rows = connection.execute(ordered_select_sql(connection, table_name)).fetchall()
    if not rows:
        return [f"-- No rows in table: {table_name}"]

    columns = rows[0].keys()
    column_sql = ", ".join(columns)
    statements = [f"-- Table: {table_name}"]

    for row in rows:
        value_sql = ", ".join(quote_sqlite_value(row[column]) for column in columns)
        statements.append(f"INSERT INTO {table_name} ({column_sql}) VALUES ({value_sql});")

    return statements


def build_export_sql(database_path: Path) -> str:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        chunks = [
            "-- Agentic Product Studio",
            "-- SQLite to Cloudflare D1 data export",
            f"-- Source database: {database_path.as_posix()}",
            "",
        ]

        for table_name in TABLE_EXPORT_ORDER:
            chunks.extend(export_table(connection, table_name))
            chunks.append("")

        return "\n".join(chunks)
    finally:
        connection.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export SQLite data into D1-friendly INSERT SQL statements."
    )
    parser.add_argument(
        "--database",
        default="instance/app.db",
        help="Source SQLite database path. Defaults to instance/app.db",
    )
    parser.add_argument(
        "--output",
        default="database/d1/data.sql",
        help="Output SQL file path. Defaults to database/d1/data.sql",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    database_path = Path(args.database)
    output_path = Path(args.output)

    if not database_path.exists():
        raise SystemExit(f"Source database not found: {database_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_export_sql(database_path), encoding="utf-8")
    print(f"D1 data export written to {output_path}")


if __name__ == "__main__":
    main()
