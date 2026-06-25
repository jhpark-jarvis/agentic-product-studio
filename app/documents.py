from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .constants import DOCUMENT_TYPES
from .db import get_db, sync_document_tags, sync_task_documents_for_document
from .utils import markdown_to_html


bp = Blueprint("documents", __name__, url_prefix="/documents")


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


def _document_form_data():
    related_task_ids = request.form.getlist("related_task_ids")
    return {
        "title": request.form.get("title", "").strip(),
        "doc_type": request.form.get("doc_type", "기타"),
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
        errors.append("문서 내용은 비워둘 수 없습니다.")
    return errors


def _fetch_document(document_id: int):
    db = get_db()
    document = db.execute(
        """
        SELECT d.*, m.name AS author_name
        FROM documents d
        LEFT JOIN members m ON m.id = d.author_id
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


@bp.route("/")
def list_documents():
    db = get_db()
    search = request.args.get("q", "").strip()
    doc_type = request.args.get("doc_type", "").strip()
    tag = request.args.get("tag", "").strip()

    clauses = []
    params: list[str] = []
    joins = ["LEFT JOIN members m ON m.id = d.author_id"]

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

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    documents = db.execute(
        f"""
        SELECT DISTINCT d.id, d.title, d.doc_type, d.updated_at, m.name AS author_name
        FROM documents d
        {' '.join(joins)}
        {where_sql}
        ORDER BY d.updated_at DESC, d.id DESC
        """,
        params,
    ).fetchall()

    tag_options = db.execute(
        """
        SELECT tag, COUNT(*) AS usage_count
        FROM document_tags
        GROUP BY tag
        ORDER BY tag COLLATE NOCASE ASC
        """
    ).fetchall()

    return render_template(
        "documents/list.html",
        documents=documents,
        document_types=DOCUMENT_TYPES,
        tag_options=tag_options,
        filters={"q": search, "doc_type": doc_type, "tag": tag},
    )


@bp.route("/new", methods=("GET", "POST"))
def create_document():
    db = get_db()
    if request.method == "POST":
        data = _document_form_data()
        errors = _validate_document_form(data)
        if not errors:
            cursor = db.execute(
                """
                INSERT INTO documents (title, doc_type, content, author_id, tags, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    data["title"],
                    data["doc_type"],
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
        "documents/form.html",
        page_title="새 문서 작성",
        submit_label="문서 저장",
        document=None,
        selected_task_ids=[] if form_data is None else form_data["related_task_ids"],
        document_types=DOCUMENT_TYPES,
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
    )


@bp.route("/<int:document_id>")
def detail(document_id: int):
    document, related_tasks, tags = _fetch_document(document_id)
    if not document:
        flash("문서를 찾을 수 없습니다.", "error")
        return redirect(url_for("documents.list_documents"))

    return render_template(
        "documents/detail.html",
        document=document,
        related_tasks=related_tasks,
        tags=tags,
        rendered_content=markdown_to_html(document["content"]),
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
            db.execute(
                """
                UPDATE documents
                SET title = ?, doc_type = ?, content = ?, author_id = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    data["title"],
                    data["doc_type"],
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
        "documents/form.html",
        page_title="문서 수정",
        submit_label="변경 저장",
        document=document,
        selected_task_ids=selected_task_ids,
        document_types=DOCUMENT_TYPES,
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
        existing_tags=", ".join(tags),
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
