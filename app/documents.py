from __future__ import annotations

from flask import Blueprint, jsonify, request

from .db import get_db
from .repositories.provider import get_repository_provider
from .storage import is_allowed_image, upload_image
from .utils import format_markdown_code_blocks, markdown_to_html, parse_int


bp = Blueprint("documents", __name__, url_prefix="/documents")


@bp.route("/preview-markdown", methods=("POST",))
def preview_markdown():
    content = request.form.get("content", "")
    return jsonify({"html": str(markdown_to_html(content))})


@bp.route("/format-markdown", methods=("POST",))
def format_markdown():
    content = request.form.get("content", "")
    return jsonify({"content": format_markdown_code_blocks(content)})


@bp.route("/search-links")
def search_document_links():
    keyword = request.args.get("q", "").strip()
    limit = min(parse_int(request.args.get("limit"), default=10, minimum=1), 20)
    rows = get_repository_provider().documents.search_documents_for_link(
        keyword=keyword,
        limit=limit,
    )
    return jsonify(
        {
            "items": [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "doc_type": row["doc_type"],
                    "is_hidden": bool(row["is_hidden"]),
                    "folder_name": row["folder_name"],
                    "updated_at": row["updated_at"],
                    "path": f"/documents/{row['id']}",
                }
                for row in rows
            ]
        }
    )


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
