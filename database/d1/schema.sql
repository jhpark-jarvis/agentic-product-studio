-- Agentic Product Studio
-- Cloudflare D1 baseline schema
-- Generated from the current operational SQLite structure and normalized
-- for future wrangler-based migrations.

CREATE TABLE members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT,
    part TEXT,
    contact TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wbs_tasks (
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

CREATE TABLE document_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_type, name)
);

CREATE TABLE documents (
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

CREATE TABLE document_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag TEXT NOT NULL
);

CREATE TABLE document_assets (
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

CREATE TABLE task_documents (
    task_id INTEGER NOT NULL REFERENCES wbs_tasks(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, document_id)
);

CREATE TABLE schedules (
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

CREATE TABLE notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_pinned INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assets (
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

CREATE TABLE asset_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(path)
);

CREATE TABLE asset_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    tag TEXT NOT NULL
);

CREATE INDEX idx_wbs_tasks_status ON wbs_tasks(status);
CREATE INDEX idx_wbs_tasks_assignee_id ON wbs_tasks(assignee_id);
CREATE INDEX idx_wbs_tasks_due_date ON wbs_tasks(due_date);
CREATE INDEX idx_wbs_tasks_updated_at ON wbs_tasks(updated_at);

CREATE INDEX idx_documents_updated_at ON documents(updated_at);
CREATE INDEX idx_documents_hidden_updated_at ON documents(is_hidden, updated_at DESC, id DESC);
CREATE INDEX idx_documents_doc_type_folder_id ON documents(doc_type, folder_id);
CREATE INDEX idx_documents_author_id ON documents(author_id);

CREATE INDEX idx_document_tags_document_id ON document_tags(document_id);
CREATE INDEX idx_document_tags_tag ON document_tags(tag);

CREATE INDEX idx_document_assets_document_id_created_at ON document_assets(document_id, created_at);
CREATE INDEX idx_document_assets_draft_key ON document_assets(draft_key);
CREATE INDEX idx_assets_updated_at ON assets(updated_at DESC, id DESC);
CREATE INDEX idx_assets_status_hidden ON assets(status, is_hidden, updated_at DESC, id DESC);
CREATE INDEX idx_assets_type_category ON assets(asset_type, category);
CREATE INDEX idx_asset_groups_path ON asset_groups(path);
CREATE INDEX idx_asset_tags_asset_id ON asset_tags(asset_id);
CREATE INDEX idx_asset_tags_tag ON asset_tags(tag);

CREATE INDEX idx_schedules_start_date ON schedules(start_date);
CREATE INDEX idx_schedules_assignee_id ON schedules(assignee_id);
CREATE INDEX idx_schedules_wbs_task_id ON schedules(wbs_task_id);

CREATE INDEX idx_task_documents_document_id ON task_documents(document_id);
