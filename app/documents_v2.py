from __future__ import annotations

from urllib.parse import urlencode

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from .constants import DOCUMENT_TYPES
from .db import (
    ensure_document_folder,
    get_db,
    sync_document_tags,
    sync_task_documents_for_document,
)
from .utils import build_pagination, format_markdown_code_blocks, markdown_to_html, parse_int


bp = Blueprint("documents", __name__, url_prefix="/documents")
PER_PAGE_OPTIONS = (10, 20, 50, 100)


def _fetch_members():
    return get_db().execute(
        "SELECT id, name FROM members WHERE is_active = 1 ORDER BY name COLLATE NOCASE ASC"
    ).fetchall()


def _fetch_tasks():
    return get_db().execute(
        """
        SELECT id, title, status
        FROM wbs_tasks
        ORDER BY updated_at DESC, id DESC
        """
    ).fetchall()


def _fetch_document_folders(doc_type: str | None = None):
    db = get_db()
    if doc_type:
        return db.execute(
            """
            SELECT id, doc_type, name
            FROM document_folders
            WHERE doc_type = ?
            ORDER BY name COLLATE NOCASE ASC
            """,
            (doc_type,),
        ).fetchall()
    return db.execute(
        """
        SELECT id, doc_type, name
        FROM document_folders
        ORDER BY doc_type COLLATE NOCASE ASC, name COLLATE NOCASE ASC
        """
    ).fetchall()


def _document_form_data():
    related_task_ids = request.form.getlist("related_task_ids")
    return {
        "title": request.form.get("title", "").strip(),
        "doc_type": request.form.get("doc_type", DOCUMENT_TYPES[-1]),
        "folder_id": request.form.get("folder_id") or None,
        "new_folder_name": request.form.get("new_folder_name", "").strip(),
        "content": request.form.get("content", "").strip(),
        "author_id": request.form.get("author_id") or None,
        "tags": request.form.get("tags", "").strip(),
        "related_task_ids": [int(value) for value in related_task_ids if value.isdigit()],
    }


def _validate_document_form(data):
    errors = []
    if not data["title"]:
        errors.append("문서 제목은 필수입니다.")
    if data["doc_type"] not in DOCUMENT_TYPES:
        errors.append("유효하지 않은 문서 유형입니다.")
    if not data["content"]:
        errors.append("문서 내용이 비어 있습니다.")
    if data["folder_id"] and not str(data["folder_id"]).isdigit():
        errors.append("유효하지 않은 폴더입니다.")
    return errors


def _resolve_folder_id(db, data):
    if data["new_folder_name"]:
        return ensure_document_folder(db, data["doc_type"], data["new_folder_name"])
    if data["folder_id"]:
        return int(data["folder_id"])
    return None


def _fetch_document(document_id: int):
    db = get_db()
    document = db.execute(
        """
        SELECT d.*, m.name AS author_name, f.name AS folder_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
        LEFT JOIN document_folders f ON f.id = d.folder_id
        WHERE d.id = ?
        """,
        (document_id,),
    ).fetchone()
    if not document:
        return None, [], []

    related_tasks = db.execute(
        """
        SELECT t.id, t.title, t.status, t.priority
        FROM task_documents td
        JOIN wbs_tasks t ON t.id = td.task_id
        WHERE td.document_id = ?
        ORDER BY t.updated_at DESC, t.id DESC
        """,
        (document_id,),
    ).fetchall()
    tag_rows = db.execute(
        "SELECT tag FROM document_tags WHERE document_id = ? ORDER BY tag COLLATE NOCASE ASC",
        (document_id,),
    ).fetchall()
    return document, related_tasks, [row["tag"] for row in tag_rows]


def _pager_query(filters, page, per_page):
    query = {key: value for key, value in filters.items() if value}
    query["page"] = page
    query["per_page"] = per_page
    return urlencode(query)


@bp.route("/")
def list_documents():
    db = get_db()
    search = request.args.get("q", "").strip()
    doc_type = request.args.get("doc_type", "").strip()
    tag = request.args.get("tag", "").strip()
    folder_id = request.args.get("folder_id", "").strip()
    page = parse_int(request.args.get("page"), default=1, minimum=1)
    per_page = parse_int(request.args.get("per_page"), default=20, allowed=set(PER_PAGE_OPTIONS))

    clauses = []
    params: list[str] = []
    joins = [
        "LEFT JOIN members m ON m.id = d.author_id",
        "LEFT JOIN document_folders f ON f.id = d.folder_id",
    ]

    if search:
        clauses.append("(d.title LIKE ? OR d.content LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if doc_type:
        clauses.append("d.doc_type = ?")
        params.append(doc_type)
    if tag:
        joins.append("JOIN document_tags dt_filter ON dt_filter.document_id = d.id")
        clauses.append("dt_filter.tag = ?")
        params.append(tag)
    if folder_id and folder_id.isdigit():
        clauses.append("d.folder_id = ?")
        params.append(folder_id)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    total_count = db.execute(
        f"""
        SELECT COUNT(DISTINCT d.id) AS count
        FROM documents d
        {' '.join(joins)}
        {where_sql}
        """,
        params,
    ).fetchone()["count"]
    pagination = build_pagination(page, per_page, total_count)

    documents = db.execute(
        f"""
        SELECT DISTINCT
            d.id,
            d.title,
            d.doc_type,
            d.updated_at,
            m.name AS author_name,
            f.id AS folder_id,
            f.name AS folder_name
        FROM documents d
        {' '.join(joins)}
        {where_sql}
        ORDER BY d.updated_at DESC, d.id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, pagination["per_page"], pagination["offset"]],
    ).fetchall()

    tag_options = db.execute(
        """
        SELECT tag, COUNT(*) AS usage_count
        FROM document_tags
        GROUP BY tag
        ORDER BY tag COLLATE NOCASE ASC
        """
    ).fetchall()

    filters = {"q": search, "doc_type": doc_type, "tag": tag, "folder_id": folder_id}
    return render_template(
        "documents/list_v2.html",
        documents=documents,
        document_types=DOCUMENT_TYPES,
        folder_options=_fetch_document_folders(doc_type or None),
        tag_options=tag_options,
        filters=filters,
        per_page_options=PER_PAGE_OPTIONS,
        pagination=pagination,
        pager_query=_pager_query,
    )


@bp.route("/new", methods=("GET", "POST"))
def create_document():
    db = get_db()
    if request.method == "POST":
        data = _document_form_data()
        errors = _validate_document_form(data)
        if not errors:
            folder_id = _resolve_folder_id(db, data)
            cursor = db.execute(
                """
                INSERT INTO documents (title, doc_type, folder_id, content, author_id, tags, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    data["title"],
                    data["doc_type"],
                    folder_id,
                    data["content"],
                    data["author_id"],
                    data["tags"],
                ),
            )
            document_id = cursor.lastrowid
            sync_document_tags(db, document_id, data["tags"])
            sync_task_documents_for_document(db, document_id, data["related_task_ids"])
            db.commit()
            flash("문서가 생성되었습니다.", "success")
            return redirect(url_for("documents.list_documents"))
        for error in errors:
            flash(error, "error")
        form_data = data
    else:
        form_data = None

    return render_template(
        "documents/form_v2.html",
        page_title="새 문서 작성",
        submit_label="문서 저장",
        document=None,
        selected_task_ids=[] if form_data is None else form_data["related_task_ids"],
        document_types=DOCUMENT_TYPES,
        document_folders=_fetch_document_folders(),
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
        selected_type=form_data["doc_type"] if form_data else DOCUMENT_TYPES[0],
    )


@bp.route("/<int:document_id>")
def detail(document_id: int):
    document, related_tasks, tags = _fetch_document(document_id)
    if not document:
        flash("문서를 찾을 수 없습니다.", "error")
        return redirect(url_for("documents.list_documents"))

    content = document["content"] or ""
    word_count = len(content.split())
    heading_count = sum(1 for line in content.splitlines() if line.lstrip().startswith("#"))

    return render_template(
        "documents/detail.html",
        document=document,
        related_tasks=related_tasks,
        tags=tags,
        rendered_content=markdown_to_html(document["content"]),
        word_count=word_count,
        heading_count=heading_count,
    )


@bp.route("/<int:document_id>/edit", methods=("GET", "POST"))
def edit_document(document_id: int):
    db = get_db()
    document, related_tasks, tags = _fetch_document(document_id)
    if not document:
        flash("문서를 찾을 수 없습니다.", "error")
        return redirect(url_for("documents.list_documents"))

    selected_task_ids = [task["id"] for task in related_tasks]
    if request.method == "POST":
        data = _document_form_data()
        errors = _validate_document_form(data)
        if not errors:
            folder_id = _resolve_folder_id(db, data)
            db.execute(
                """
                UPDATE documents
                SET title = ?, doc_type = ?, folder_id = ?, content = ?, author_id = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    data["title"],
                    data["doc_type"],
                    folder_id,
                    data["content"],
                    data["author_id"],
                    data["tags"],
                    document_id,
                ),
            )
            sync_document_tags(db, document_id, data["tags"])
            sync_task_documents_for_document(db, document_id, data["related_task_ids"])
            db.commit()
            flash("문서가 수정되었습니다.", "success")
            return redirect(url_for("documents.detail", document_id=document_id))
        for error in errors:
            flash(error, "error")
        form_data = data
        selected_task_ids = data["related_task_ids"]
    else:
        form_data = None

    return render_template(
        "documents/form_v2.html",
        page_title="문서 수정",
        submit_label="변경 저장",
        document=document,
        selected_task_ids=selected_task_ids,
        document_types=DOCUMENT_TYPES,
        document_folders=_fetch_document_folders(),
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
        existing_tags=", ".join(tags),
        selected_type=(form_data["doc_type"] if form_data else document["doc_type"]),
    )


@bp.route("/<int:document_id>/delete", methods=("POST",))
def delete_document(document_id: int):
    db = get_db()
    db.execute("DELETE FROM task_documents WHERE document_id = ?", (document_id,))
    db.execute("DELETE FROM document_tags WHERE document_id = ?", (document_id,))
    db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    db.commit()
    flash("문서가 삭제되었습니다.", "success")
    return redirect(url_for("documents.list_documents"))


@bp.route("/preview-markdown", methods=("POST",))
def preview_markdown():
    content = request.form.get("content", "")
    return jsonify({"html": str(markdown_to_html(content))})


@bp.route("/format-markdown", methods=("POST",))
def format_markdown():
    content = request.form.get("content", "")
    return jsonify({"content": format_markdown_code_blocks(content)})
