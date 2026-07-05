from __future__ import annotations

from urllib.parse import urlencode
from uuid import uuid4

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from .constants import DOCUMENT_TYPES
from .db import get_db
from .repositories.provider import get_repository_provider
from .storage import delete_object, is_allowed_image, upload_image
from .utils import build_pagination, format_markdown_code_blocks, markdown_to_html, parse_int


bp = Blueprint("documents", __name__, url_prefix="/documents")
PER_PAGE_OPTIONS = (10, 20, 50, 100)


def _fetch_members():
    return get_repository_provider().common.fetch_active_members()


def _fetch_tasks():
    return get_repository_provider().common.fetch_task_link_options()


def _fetch_document_folders(doc_type: str | None = None):
    return get_repository_provider().documents.fetch_document_folders(doc_type)


def _fetch_folder(folder_id: int):
    return get_repository_provider().documents.fetch_folder(folder_id)


def _document_form_data():
    related_task_ids = request.form.getlist("related_task_ids")
    return {
        "asset_draft_key": request.form.get("asset_draft_key", "").strip(),
        "title": request.form.get("title", "").strip(),
        "doc_type": request.form.get("doc_type", DOCUMENT_TYPES[-1]),
        "folder_id": request.form.get("folder_id") or None,
        "new_folder_name": request.form.get("new_folder_name", "").strip(),
        "content": request.form.get("content", "").strip(),
        "author_id": request.form.get("author_id") or None,
        "tags": request.form.get("tags", "").strip(),
        "is_hidden": 1 if request.form.get("is_hidden") else 0,
        "related_task_ids": [int(value) for value in related_task_ids if value.isdigit()],
    }


def _validate_document_form(data):
    errors = []
    if not data["title"]:
        errors.append("문서 제목은 필수입니다.")
    if data["doc_type"] not in DOCUMENT_TYPES:
        errors.append("유효하지 않은 문서 유형입니다.")
    if not data["content"]:
        errors.append("문서 내용을 입력해주세요.")
    if data["folder_id"] and not str(data["folder_id"]).isdigit():
        errors.append("유효하지 않은 폴더입니다.")
    return errors


def _resolve_folder_id(db, data):
    if data["new_folder_name"]:
        return get_repository_provider().documents.ensure_folder(
            data["doc_type"], data["new_folder_name"]
        )
    if data["folder_id"]:
        return int(data["folder_id"])
    return None


def _fetch_document(document_id: int):
    document, related_tasks, tags = get_repository_provider().documents.fetch_document_with_relations(
        document_id
    )
    if not document:
        return None, [], [], []
    assets = get_repository_provider().documents.fetch_document_assets(document_id)
    return document, related_tasks, tags, assets


def _pager_query(filters, page, per_page):
    query = {key: value for key, value in filters.items() if value not in ("", None)}
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

    total_count, documents = get_repository_provider().documents.list_documents(
        search=search,
        doc_type=doc_type,
        tag=tag,
        folder_id=folder_id,
        limit=per_page,
        offset=0,
    )
    pagination = build_pagination(page, per_page, total_count)
    _total_count, documents = get_repository_provider().documents.list_documents(
        search=search,
        doc_type=doc_type,
        tag=tag,
        folder_id=folder_id,
        limit=pagination["per_page"],
        offset=pagination["offset"],
    )

    tag_options = get_repository_provider().documents.fetch_tag_options()

    filters = {"q": search, "doc_type": doc_type, "tag": tag, "folder_id": folder_id}
    return render_template(
        "documents/list.html",
        documents=documents,
        document_types=DOCUMENT_TYPES,
        folder_options=_fetch_document_folders(doc_type or None),
        all_folder_options=_fetch_document_folders(),
        tag_options=tag_options,
        filters=filters,
        per_page_options=PER_PAGE_OPTIONS,
        pagination=pagination,
        pager_query=_pager_query,
    )


@bp.route("/new", methods=("GET", "POST"))
def create_document():
    if request.method == "POST":
        data = _document_form_data()
        errors = _validate_document_form(data)
        if not errors:
            folder_id = _resolve_folder_id(get_db(), data)
            document_id = get_repository_provider().documents.create_document(data, folder_id)
            get_repository_provider().documents.assign_draft_assets(
                document_id, data["asset_draft_key"]
            )
            get_repository_provider().documents.sync_document_tags(document_id, data["tags"])
            get_repository_provider().documents.sync_task_documents(
                document_id, data["related_task_ids"]
            )
            get_db().commit()
            flash("문서가 생성되었습니다.", "success")
            return redirect(url_for("documents.list_documents"))
        for error in errors:
            flash(error, "error")
        form_data = data
    else:
        form_data = None

    return render_template(
        "documents/form.html",
        page_title="새 문서",
        submit_label="문서 저장",
        document=None,
        selected_task_ids=[] if form_data is None else form_data["related_task_ids"],
        document_types=DOCUMENT_TYPES,
        document_folders=_fetch_document_folders(),
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
        selected_type=form_data["doc_type"] if form_data else DOCUMENT_TYPES[0],
        asset_draft_key=(form_data["asset_draft_key"] if form_data else uuid4().hex),
    )


@bp.route("/<int:document_id>")
def detail(document_id: int):
    document, related_tasks, tags, assets = _fetch_document(document_id)
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
        assets=assets,
        rendered_content=markdown_to_html(document["content"]),
        word_count=word_count,
        heading_count=heading_count,
    )


@bp.route("/<int:document_id>/edit", methods=("GET", "POST"))
def edit_document(document_id: int):
    document, related_tasks, tags, _assets = _fetch_document(document_id)
    if not document:
        flash("문서를 찾을 수 없습니다.", "error")
        return redirect(url_for("documents.list_documents"))

    selected_task_ids = [task["id"] for task in related_tasks]
    if request.method == "POST":
        data = _document_form_data()
        errors = _validate_document_form(data)
        if not errors:
            folder_id = _resolve_folder_id(get_db(), data)
            get_repository_provider().documents.update_document(document_id, data, folder_id)
            get_repository_provider().documents.sync_document_tags(document_id, data["tags"])
            get_repository_provider().documents.sync_task_documents(
                document_id, data["related_task_ids"]
            )
            get_db().commit()
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
        document_folders=_fetch_document_folders(),
        members=_fetch_members(),
        tasks=_fetch_tasks(),
        form_data=form_data,
        existing_tags=", ".join(tags),
        selected_type=(form_data["doc_type"] if form_data else document["doc_type"]),
        asset_draft_key=(form_data["asset_draft_key"] if form_data else ""),
    )


@bp.route("/<int:document_id>/delete", methods=("POST",))
def delete_document(document_id: int):
    db = get_db()
    assets = get_repository_provider().documents.fetch_document_assets(document_id)
    for asset in assets:
        delete_object(asset["object_key"])
    get_repository_provider().documents.delete_document(document_id)
    db.commit()
    flash("문서가 삭제되었습니다.", "success")
    return redirect(url_for("documents.list_documents"))


@bp.route("/folders", methods=("POST",))
def create_folder():
    doc_type = request.form.get("doc_type", "").strip()
    folder_name = request.form.get("folder_name", "").strip()
    redirect_url = request.form.get("redirect_to") or url_for("documents.list_documents")

    if doc_type not in DOCUMENT_TYPES:
        flash("유효하지 않은 문서 카테고리입니다.", "error")
        return redirect(redirect_url)
    if not folder_name:
        flash("폴더 이름을 입력해주세요.", "error")
        return redirect(redirect_url)

    get_repository_provider().documents.ensure_folder(doc_type, folder_name)
    get_db().commit()
    flash("폴더가 생성되었습니다.", "success")
    return redirect(redirect_url)


@bp.route("/<int:document_id>/folder", methods=("POST",))
def update_document_folder(document_id: int):
    db = get_db()
    document, _, _, _ = _fetch_document(document_id)
    if not document:
        flash("문서를 찾을 수 없습니다.", "error")
        return redirect(url_for("documents.list_documents"))

    redirect_url = request.form.get("redirect_to") or url_for("documents.list_documents")
    doc_type = request.form.get("doc_type", "").strip() or document["doc_type"]
    if doc_type not in DOCUMENT_TYPES:
        flash("유효하지 않은 문서 카테고리입니다.", "error")
        return redirect(redirect_url)

    folder_id_raw = (request.form.get("folder_id") or "").strip()
    folder_id = None
    if folder_id_raw:
        if not folder_id_raw.isdigit():
            flash("유효하지 않은 폴더입니다.", "error")
            return redirect(redirect_url)
        folder = _fetch_folder(int(folder_id_raw))
        if not folder:
            flash("선택한 폴더를 찾을 수 없습니다.", "error")
            return redirect(redirect_url)
        if folder["doc_type"] != doc_type:
            flash("문서 카테고리와 폴더 카테고리가 일치하지 않습니다.", "error")
            return redirect(redirect_url)
        folder_id = folder["id"]

    get_repository_provider().documents.update_document_folder(document_id, doc_type, folder_id)
    db.commit()
    flash("문서 카테고리와 폴더가 변경되었습니다.", "success")
    return redirect(redirect_url)


@bp.route("/preview-markdown", methods=("POST",))
def preview_markdown():
    content = request.form.get("content", "")
    return jsonify({"html": str(markdown_to_html(content))})


@bp.route("/format-markdown", methods=("POST",))
def format_markdown():
    content = request.form.get("content", "")
    return jsonify({"content": format_markdown_code_blocks(content)})


@bp.route("/upload-image", methods=("POST",))
def upload_markdown_image():
    db = get_db()
    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify({"error": "업로드할 이미지 파일이 없습니다."}), 400
    if not is_allowed_image(image.filename):
        return jsonify({"error": "지원하지 않는 이미지 형식입니다."}), 400

    document_id_raw = (request.form.get("document_id") or "").strip()
    document_id = int(document_id_raw) if document_id_raw.isdigit() else None
    draft_key = request.form.get("draft_key", "").strip() or None
    uploaded = upload_image(image, folder="documents")
    asset_id = get_repository_provider().documents.create_document_asset(
        document_id=document_id,
        draft_key=draft_key,
        object_key=uploaded["object_key"],
        url=uploaded["url"],
        original_filename=image.filename,
        content_type=uploaded["content_type"],
        size=int(uploaded["size"]),
    )
    db.commit()
    alt = request.form.get("alt", "").strip() or image.filename.rsplit(".", 1)[0]
    return jsonify(
        {
            "asset_id": asset_id,
            "url": uploaded["url"],
            "object_key": uploaded["object_key"],
            "markdown": f"![{alt}]({uploaded['url']})",
        }
    )


@bp.route("/<int:document_id>/assets/<int:asset_id>/delete", methods=("POST",))
def delete_document_asset(document_id: int, asset_id: int):
    db = get_db()
    asset = get_repository_provider().documents.fetch_document_asset(asset_id)
    if not asset or asset["document_id"] != document_id:
        flash("이미지 자산을 찾을 수 없습니다.", "error")
        return redirect(url_for("documents.detail", document_id=document_id))

    delete_object(asset["object_key"])
    get_repository_provider().documents.delete_document_asset(asset_id)
    db.commit()
    flash("문서 이미지가 삭제되었습니다.", "success")
    return redirect(url_for("documents.detail", document_id=document_id))
