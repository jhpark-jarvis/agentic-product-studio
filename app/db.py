import sqlite3
from pathlib import Path

import click


def _has_flask_app_context() -> bool:
    try:
        from flask import has_app_context
    except ImportError:
        return False
    return has_app_context()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT,
    part TEXT,
    contact TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wbs_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER REFERENCES wbs_tasks(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    assignee_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
    platform TEXT DEFAULT 'Agentic Product Studio',
    status TEXT NOT NULL DEFAULT '예정',
    priority TEXT NOT NULL DEFAULT '보통',
    start_date TEXT,
    due_date TEXT,
    completed_date TEXT,
    progress INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    folder_id INTEGER REFERENCES document_folders(id) ON DELETE SET NULL,
    is_hidden INTEGER NOT NULL DEFAULT 0,
    file_name TEXT,
    notes TEXT,
    content TEXT DEFAULT '',
    author_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
    tags TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_type, name)
);

CREATE TABLE IF NOT EXISTS task_documents (
    task_id INTEGER NOT NULL REFERENCES wbs_tasks(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, document_id)
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    assignee_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
    wbs_task_id INTEGER REFERENCES wbs_tasks(id) ON DELETE SET NULL,
    schedule_type TEXT NOT NULL DEFAULT '개발',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_pinned INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    asset_type TEXT DEFAULT '',
    category TEXT DEFAULT '',
    file_name TEXT NOT NULL,
    original_filename TEXT NOT NULL DEFAULT '',
    object_key TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    content_type TEXT,
    size INTEGER NOT NULL DEFAULT 0,
    checksum TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT '사용 가능',
    is_hidden INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER REFERENCES members(id) ON DELETE SET NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asset_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(path)
);

CREATE TABLE IF NOT EXISTS asset_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS avatar_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type TEXT NOT NULL,
    gender TEXT NOT NULL,
    name TEXT NOT NULL,
    source_index INTEGER NOT NULL DEFAULT 0,
    availability TEXT NOT NULL DEFAULT '',
    match_status TEXT NOT NULL DEFAULT '',
    series TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT '',
    master_resource_id TEXT NOT NULL,
    group_id TEXT NOT NULL DEFAULT '',
    group_size INTEGER NOT NULL DEFAULT 1,
    master_color_hex TEXT NOT NULL DEFAULT '',
    master_is_group_canonical INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_type, gender, master_resource_id)
);

CREATE TABLE IF NOT EXISTS avatar_asset_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avatar_asset_id INTEGER NOT NULL REFERENCES avatar_assets(id) ON DELETE CASCADE,
    resource_id TEXT NOT NULL,
    thumbnail_url TEXT NOT NULL DEFAULT '',
    hex_code TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    dname TEXT NOT NULL DEFAULT '',
    UNIQUE(avatar_asset_id, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_avatar_assets_type_gender ON avatar_assets(asset_type, gender);
CREATE INDEX IF NOT EXISTS idx_avatar_assets_name ON avatar_assets(name);
CREATE INDEX IF NOT EXISTS idx_avatar_asset_variants_asset_id ON avatar_asset_variants(avatar_asset_id);
CREATE INDEX IF NOT EXISTS idx_avatar_asset_variants_resource_id ON avatar_asset_variants(resource_id);

CREATE TABLE IF NOT EXISTS document_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    draft_key TEXT,
    object_key TEXT NOT NULL,
    url TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    content_type TEXT,
    size INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


_RUNTIME_DB_CONNECTION = None


def get_db():
    if _has_flask_app_context():
        from flask import current_app, g

        if "db" not in g:
            g.db = connect_sqlite_database(current_app.config["DATABASE"])
        return g.db

    if _RUNTIME_DB_CONNECTION is None:
        raise RuntimeError("Database connection is not initialized for the current runtime.")
    return _RUNTIME_DB_CONNECTION


def close_db(_error=None):
    from flask import g

    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    initialize_database(db)


def connect_sqlite_database(database_path: str | Path):
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize_database(db):
    db.executescript(SCHEMA_SQL)
    migrate_legacy_schema(db)
    db.commit()


def initialize_sqlite_database(database_path: str | Path):
    db = connect_sqlite_database(database_path)
    try:
        initialize_database(db)
    finally:
        db.close()


def set_runtime_db_connection(db):
    global _RUNTIME_DB_CONNECTION
    _RUNTIME_DB_CONNECTION = db


def clear_runtime_db_connection():
    global _RUNTIME_DB_CONNECTION
    _RUNTIME_DB_CONNECTION = None


def _table_exists(db, table_name):
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_names(db, table_name):
    return {row["name"] for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _add_column_if_missing(db, table_name, column_name, column_sql):
    if column_name not in _column_names(db, table_name):
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def migrate_legacy_schema(db):
    if _table_exists(db, "documents"):
        _add_column_if_missing(db, "documents", "content", "TEXT DEFAULT ''")
        _add_column_if_missing(db, "documents", "author_id", "INTEGER")
        _add_column_if_missing(db, "documents", "tags", "TEXT DEFAULT ''")
        _add_column_if_missing(db, "documents", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        _add_column_if_missing(db, "documents", "folder_id", "INTEGER")
        _add_column_if_missing(db, "documents", "is_hidden", "INTEGER NOT NULL DEFAULT 0")
    if _table_exists(db, "wbs_tasks"):
        _add_column_if_missing(db, "wbs_tasks", "platform", "TEXT DEFAULT 'Agentic Product Studio'")
    if _table_exists(db, "document_assets"):
        _add_column_if_missing(db, "document_assets", "draft_key", "TEXT")
        _add_column_if_missing(db, "document_assets", "object_key", "TEXT")
        _add_column_if_missing(db, "document_assets", "url", "TEXT")
        _add_column_if_missing(db, "document_assets", "original_filename", "TEXT")
        _add_column_if_missing(db, "document_assets", "content_type", "TEXT")
        _add_column_if_missing(db, "document_assets", "size", "INTEGER NOT NULL DEFAULT 0")
    if _table_exists(db, "assets"):
        _add_column_if_missing(db, "assets", "asset_type", "TEXT DEFAULT ''")
        _add_column_if_missing(db, "assets", "category", "TEXT DEFAULT ''")
        _add_column_if_missing(db, "assets", "original_filename", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "assets", "object_key", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "assets", "url", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(db, "assets", "content_type", "TEXT")
        _add_column_if_missing(db, "assets", "size", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(db, "assets", "checksum", "TEXT DEFAULT ''")
        _add_column_if_missing(db, "assets", "status", "TEXT NOT NULL DEFAULT '사용 가능'")
        _add_column_if_missing(db, "assets", "is_hidden", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(db, "assets", "created_by", "INTEGER")
        _add_column_if_missing(db, "assets", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS asset_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(path)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS asset_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
            tag TEXT NOT NULL
        )
        """
    )
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS avatar_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT NOT NULL,
            gender TEXT NOT NULL,
            name TEXT NOT NULL,
            source_index INTEGER NOT NULL DEFAULT 0,
            availability TEXT NOT NULL DEFAULT '',
            match_status TEXT NOT NULL DEFAULT '',
            series TEXT NOT NULL DEFAULT '',
            confidence TEXT NOT NULL DEFAULT '',
            master_resource_id TEXT NOT NULL,
            group_id TEXT NOT NULL DEFAULT '',
            group_size INTEGER NOT NULL DEFAULT 1,
            master_color_hex TEXT NOT NULL DEFAULT '',
            master_is_group_canonical INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(asset_type, gender, master_resource_id)
        );
        CREATE TABLE IF NOT EXISTS avatar_asset_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avatar_asset_id INTEGER NOT NULL REFERENCES avatar_assets(id) ON DELETE CASCADE,
            resource_id TEXT NOT NULL,
            thumbnail_url TEXT NOT NULL DEFAULT '',
            hex_code TEXT NOT NULL DEFAULT '',
            name TEXT NOT NULL DEFAULT '',
            dname TEXT NOT NULL DEFAULT '',
            UNIQUE(avatar_asset_id, resource_id)
        );
        CREATE INDEX IF NOT EXISTS idx_avatar_assets_type_gender ON avatar_assets(asset_type, gender);
        CREATE INDEX IF NOT EXISTS idx_avatar_assets_name ON avatar_assets(name);
        CREATE INDEX IF NOT EXISTS idx_avatar_asset_variants_asset_id ON avatar_asset_variants(avatar_asset_id);
        CREATE INDEX IF NOT EXISTS idx_avatar_asset_variants_resource_id ON avatar_asset_variants(resource_id);
        """
    )


def ensure_document_folder(db, doc_type, folder_name):
    normalized_name = (folder_name or "").strip()
    if not normalized_name:
        return None

    existing = db.execute(
        """
        SELECT id
        FROM document_folders
        WHERE doc_type = ? AND lower(name) = lower(?)
        """,
        (doc_type, normalized_name),
    ).fetchone()
    if existing:
        return existing["id"]

    cursor = db.execute(
        "INSERT INTO document_folders (doc_type, name) VALUES (?, ?)",
        (doc_type, normalized_name),
    )
    return cursor.lastrowid


def normalize_tags(tags_text):
    tags = []
    for raw in (tags_text or "").split(","):
        tag = raw.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def sync_document_tags(db, document_id, tags_text):
    db.execute("DELETE FROM document_tags WHERE document_id = ?", (document_id,))
    for tag in normalize_tags(tags_text):
        db.execute(
            "INSERT INTO document_tags (document_id, tag) VALUES (?, ?)",
            (document_id, tag),
        )


def sync_asset_tags(db, asset_id, tags_text):
    db.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))
    for tag in normalize_tags(tags_text):
        db.execute(
            "INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)",
            (asset_id, tag),
        )


def sync_task_documents(db, task_id, document_ids):
    db.execute("DELETE FROM task_documents WHERE task_id = ?", (task_id,))
    for document_id in sorted(set(document_ids)):
        db.execute(
            "INSERT OR IGNORE INTO task_documents (task_id, document_id) VALUES (?, ?)",
            (task_id, document_id),
        )


def sync_task_documents_for_document(db, document_id, task_ids):
    db.execute("DELETE FROM task_documents WHERE document_id = ?", (document_id,))
    for task_id in sorted(set(task_ids)):
        db.execute(
            "INSERT OR IGNORE INTO task_documents (task_id, document_id) VALUES (?, ?)",
            (task_id, document_id),
        )


def create_document_asset(
    db,
    *,
    document_id,
    draft_key,
    object_key,
    url,
    original_filename,
    content_type,
    size,
):
    cursor = db.execute(
        """
        INSERT INTO document_assets (
            document_id, draft_key, object_key, url, original_filename, content_type, size
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (document_id, draft_key, object_key, url, original_filename, content_type, size),
    )
    return cursor.lastrowid


def assign_draft_assets_to_document(db, document_id, draft_key):
    if not draft_key:
        return

    db.execute(
        """
        UPDATE document_assets
        SET document_id = ?, draft_key = NULL
        WHERE draft_key = ? AND document_id IS NULL
        """,
        (document_id, draft_key),
    )


def fetch_document_assets(db, document_id):
    return db.execute(
        """
        SELECT id, document_id, object_key, url, original_filename, content_type, size, created_at
        FROM document_assets
        WHERE document_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (document_id,),
    ).fetchall()


def fetch_document_asset(db, asset_id):
    return db.execute(
        """
        SELECT id, document_id, draft_key, object_key, url, original_filename, content_type, size, created_at
        FROM document_assets
        WHERE id = ?
        """,
        (asset_id,),
    ).fetchone()


def delete_document_asset(db, asset_id):
    db.execute("DELETE FROM document_assets WHERE id = ?", (asset_id,))


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Initialized the database.")


@click.command("seed-sample-data")
@click.option("--force", is_flag=True, help="기존 협업 데이터가 있어도 샘플 데이터를 다시 채웁니다.")
def seed_sample_data_command(force):
    db = get_db()
    init_db()

    if not force:
        existing = db.execute("SELECT COUNT(*) AS count FROM wbs_tasks").fetchone()["count"]
        if existing:
            click.echo("Sample data skipped: existing WBS tasks found. Use --force to reseed.")
            return

    if force:
        db.executescript(
            """
            DELETE FROM task_documents;
            DELETE FROM document_tags;
            DELETE FROM schedules;
            DELETE FROM documents;
            DELETE FROM wbs_tasks;
            DELETE FROM notices;
            DELETE FROM members;
            """
        )

    members = [
        ("김기획", "기획", "콘텐츠", "planner#1001", 1),
        ("박클라", "클라이언트", "전투", "client#2001", 1),
        ("이서버", "서버", "코어", "server#3001", 1),
        ("정아트", "아트", "UI", "art#4001", 1),
    ]
    db.executemany(
        "INSERT INTO members (name, role, part, contact, is_active) VALUES (?, ?, ?, ?, ?)",
        members,
    )

    task_rows = [
        (None, "월드 개발 1차 스프린트", "초기 스프린트 전체 묶음", 1, "진행중", "높음", "2026-06-23", "2026-07-05", None, 45, "주요 작업 트래킹"),
        (1, "전투 밸런스 시나리오 정리", "기획 밸런스 시트 및 시뮬레이션", 1, "검토중", "높음", "2026-06-24", "2026-06-28", None, 80, "회의 반영 필요"),
        (1, "매칭 서버 상태 개선", "서버 지연 로그 점검과 임계치 조정", 3, "진행중", "긴급", "2026-06-24", "2026-06-27", None, 55, "배포 전 재확인"),
        (1, "튜토리얼 UI 리소스 정리", "가이드 화면 아이콘 정리", 4, "예정", "보통", "2026-06-27", "2026-07-01", None, 0, "문구 확정 후 시작"),
        (None, "라이브 준비 체크", "배포 전 공통 점검 항목", 2, "보류", "보통", "2026-06-20", "2026-06-26", None, 20, "QA 일정 재조정"),
        (5, "릴리즈 노트 취합", "기능별 변경점 문서화", 1, "완료", "보통", "2026-06-18", "2026-06-24", "2026-06-24", 100, "초안 완료"),
    ]
    db.executemany(
        """
        INSERT INTO wbs_tasks (
            parent_id, title, description, assignee_id, status, priority,
            start_date, due_date, completed_date, progress, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        task_rows,
    )

    document_rows = [
        ("전투 시스템 밸런스 기획안", "기획서", "# 밸런스 기획안\n\n- 스킬 계수 정리\n- 레벨 구간별 난이도 조정", 1, "밸런스,전투,1차"),
        ("매칭 서버 장애 대응 메모", "기술문서", "# 장애 대응\n\n1. 로그 구간 확인\n2. 병목 원인 정리\n3. 재현 테스트", 3, "서버,장애,매칭"),
        ("06-25 스프린트 회의록", "회의록", "# 회의 요약\n\n- 전투 밸런스 재검토\n- UI 일정 조정\n- 배포 체크리스트 공유", 1, "회의,스프린트"),
        ("월드 리소스 참고 링크", "참고자료", "# 참고 자료\n\n- 이펙트 레퍼런스\n- UI 구조 예시", 4, "리소스,UI,참고"),
    ]
    for title, doc_type, content, author_id, tags in document_rows:
        cursor = db.execute(
            """
            INSERT INTO documents (title, doc_type, content, author_id, tags, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (title, doc_type, content, author_id, tags),
        )
        document_id = cursor.lastrowid
        sync_document_tags(db, document_id, tags)

    task_links = [(2, 1), (3, 2), (1, 3), (4, 4), (6, 3)]
    db.executemany(
        "INSERT OR IGNORE INTO task_documents (task_id, document_id) VALUES (?, ?)",
        task_links,
    )

    schedules = [
        ("전투 밸런스 리뷰", "기획/클라이언트 공동 리뷰", "2026-06-26", "2026-06-26", 1, 2, "리뷰"),
        ("매칭 서버 패치 점검", "배포 전 체크", "2026-06-27", "2026-06-27", 3, 3, "배포"),
        ("주간 개발 스탠드업", "이번 주 이슈와 일정 공유", "2026-06-27", "2026-06-27", 2, 1, "회의"),
        ("튜토리얼 UI 정리 착수", "리소스 정리 시작", "2026-06-30", "2026-07-01", 4, 4, "개발"),
    ]
    db.executemany(
        """
        INSERT INTO schedules (title, description, start_date, end_date, assignee_id, wbs_task_id, schedule_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        schedules,
    )

    db.execute(
        """
        INSERT INTO notices (title, content, is_pinned)
        VALUES (?, ?, 1)
        """,
        (
            "이번 주 공지",
            "금요일 오후까지 각 파트별 진행률과 다음 주 리스크를 WBS 메모에 반영해주세요.\n배포 체크리스트는 일정 페이지에서 함께 확인합니다.",
        ),
    )

    db.commit()
    click.echo("Sample data inserted.")


@click.command("import-avatar-assets")
@click.option("--replace", is_flag=True, help="기존 아바타 카탈로그 데이터를 비운 뒤 전체 교체합니다.")
@click.option(
    "--input",
    "input_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=Path("database/seeds/avatar_asset_variants.csv"),
    show_default=True,
)
def import_avatar_assets_command(replace, input_path):
    from .avatar_catalog_import import load_avatar_catalog_records
    from .repositories.provider import get_repository_provider

    records = load_avatar_catalog_records(input_path)
    result = get_repository_provider().avatar_assets.replace_catalog(records, replace=replace)
    get_db().commit()
    click.echo(
        f"Avatar catalog imported: {result['asset_count']} assets, {result['variant_count']} variants."
    )


def init_app(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_sample_data_command)
    app.cli.add_command(import_avatar_assets_command)
