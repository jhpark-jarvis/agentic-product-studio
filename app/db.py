import sqlite3
from pathlib import Path

import click
from flask import current_app, g


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
    file_name TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(_error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA_SQL)
    migrate_legacy_schema(db)
    db.commit()


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


def init_app(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_sample_data_command)
