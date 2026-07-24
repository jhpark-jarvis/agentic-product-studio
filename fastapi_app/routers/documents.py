from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile

from app.constants import DOCUMENT_TYPES
from app.storage import delete_object_with_config, is_allowed_image, upload_file_from_stream
from app.utils import (
    build_pagination,
    format_markdown_code_blocks,
    markdown_to_html,
    parse_int,
)

from ..dependencies import get_repository_provider, get_runtime_sqlite_db, get_settings
from ..helpers import PER_PAGE_OPTIONS, extract_linked_document_ids, serialize_rows


router = APIRouter(prefix="/api/documents", tags=["documents"])
public_router = APIRouter(prefix="/documents", tags=["document-tools"])


def _document_form_payload(payload: dict[str, Any]):
    related_task_ids = payload.get("related_task_ids") or []
    normalized_task_ids = []
    for value in related_task_ids:
        if isinstance(value, int):
            normalized_task_ids.append(value)
        elif isinstance(value, str) and value.isdigit():
            normalized_task_ids.append(int(value))

    return {
        "asset_draft_key": (payload.get("asset_draft_key") or "").strip(),
        "title": (payload.get("title") or "").strip(),
        "doc_type": (payload.get("doc_type") or DOCUMENT_TYPES[-1]).strip(),
        "folder_id": payload.get("folder_id") or None,
        "new_folder_name": (payload.get("new_folder_name") or "").strip(),
        "content": (payload.get("content") or "").strip(),
        "author_id": payload.get("author_id") or None,
        "tags": (payload.get("tags") or "").strip(),
        "is_hidden": 1 if payload.get("is_hidden") else 0,
        "related_task_ids": normalized_task_ids,
    }


def _normalize_document_ids(values) -> list[int]:
    normalized_ids: list[int] = []
    for value in values or []:
        if isinstance(value, int) and value > 0:
            normalized_ids.append(value)
        elif isinstance(value, str) and value.isdigit():
            normalized_ids.append(int(value))
    return sorted(set(normalized_ids))


def _validate_document_payload(data):
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


def _resolve_document_folder_id(provider, data):
    if data["new_folder_name"]:
        return provider.documents.ensure_folder(data["doc_type"], data["new_folder_name"])
    if data["folder_id"]:
        return int(data["folder_id"])
    return None


@public_router.post("/preview-markdown")
async def preview_markdown(content: str = Form(default="")):
    return {"html": str(markdown_to_html(content))}


@public_router.post("/format-markdown")
async def format_markdown(content: str = Form(default="")):
    return {"content": format_markdown_code_blocks(content)}


@public_router.get("/search-links")
async def search_document_links(
    q: str = "",
    limit: int = 10,
    provider=Depends(get_repository_provider),
):
    normalized_limit = min(parse_int(limit, default=10, minimum=1), 20)
    rows = provider.documents.search_documents_for_link(keyword=q.strip(), limit=normalized_limit)
    return {
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


@public_router.post("/upload-image")
async def upload_markdown_image(
    image: UploadFile = File(...),
    document_id: str = Form(default=""),
    draft_key: str = Form(default=""),
    alt: str = Form(default=""),
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    if not image.filename:
        raise HTTPException(status_code=400, detail="업로드할 이미지 파일이 없습니다.")
    if not is_allowed_image(image.filename):
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    resolved_document_id = int(document_id) if str(document_id).strip().isdigit() else None
    resolved_draft_key = draft_key.strip() or None
    uploaded = upload_file_from_stream(
        settings.to_config_mapping(),
        filename=image.filename,
        stream=image.file,
        content_type=image.content_type,
        folder="documents",
    )
    asset_id = provider.documents.create_document_asset(
        document_id=resolved_document_id,
        draft_key=resolved_draft_key,
        object_key=uploaded["object_key"],
        url=uploaded["url"],
        original_filename=image.filename,
        content_type=uploaded["content_type"],
        size=int(uploaded["size"]),
    )
    if sqlite_db is not None:
        sqlite_db.commit()
    resolved_alt = alt.strip() or image.filename.rsplit(".", 1)[0]
    return {
        "asset_id": asset_id,
        "url": uploaded["url"],
        "object_key": uploaded["object_key"],
        "markdown": f"![{resolved_alt}]({uploaded['url']})",
    }


@router.get("")
async def documents_list(
    q: str = "",
    doc_type: str = "",
    tag: str = "",
    folder_id: str = "",
    include_hidden: str = "",
    page: int = 1,
    per_page: int = 20,
    provider=Depends(get_repository_provider),
):
    normalized_include_hidden = str(include_hidden).strip().lower() in {"1", "true", "yes", "on"}
    normalized_page = parse_int(page, default=1, minimum=1)
    normalized_per_page = parse_int(per_page, default=20, allowed=set(PER_PAGE_OPTIONS))

    total_count, documents = provider.documents.list_documents(
        search=q.strip(),
        doc_type=doc_type.strip(),
        tag=tag.strip(),
        folder_id=folder_id.strip(),
        include_hidden=normalized_include_hidden,
        limit=normalized_per_page,
        offset=max((normalized_page - 1) * normalized_per_page, 0),
    )
    pagination = build_pagination(normalized_page, normalized_per_page, total_count)
    folder_options = provider.documents.fetch_document_folders(doc_type.strip() or None)
    tag_options = provider.documents.fetch_tag_options()

    return {
        "documents": serialize_rows(documents),
        "document_types": list(DOCUMENT_TYPES),
        "folder_options": serialize_rows(folder_options),
        "tag_options": serialize_rows(tag_options),
        "pagination": pagination,
        "per_page_options": list(PER_PAGE_OPTIONS),
        "filters": {
            "q": q.strip(),
            "doc_type": doc_type.strip(),
            "tag": tag.strip(),
            "folder_id": folder_id.strip(),
            "include_hidden": normalized_include_hidden,
        },
    }


@router.get("/editor")
async def document_editor_bootstrap(
    document_id: int = Query(default=0),
    provider=Depends(get_repository_provider),
):
    normalized_document_id = parse_int(document_id, default=0, minimum=0)
    document = None
    related_tasks = []
    tags = []
    assets = []

    if normalized_document_id:
        document, related_tasks, tags = provider.documents.fetch_document_with_relations(
            normalized_document_id
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        assets = provider.documents.fetch_document_assets(normalized_document_id)

    selected_type = document["doc_type"] if document else DOCUMENT_TYPES[0]

    return {
        "document": dict(document) if document else None,
        "document_types": list(DOCUMENT_TYPES),
        "document_folders": serialize_rows(provider.documents.fetch_document_folders()),
        "members": serialize_rows(provider.common.fetch_active_members()),
        "tasks": serialize_rows(provider.common.fetch_task_link_options()),
        "related_task_ids": [task["id"] for task in related_tasks],
        "tags": list(tags),
        "assets": serialize_rows(assets),
        "selected_type": selected_type,
        "asset_draft_key": "" if document else uuid4().hex,
    }


@router.get("/{document_id}")
async def document_detail(document_id: int, provider=Depends(get_repository_provider)):
    document, related_tasks, tags = provider.documents.fetch_document_with_relations(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    assets = provider.documents.fetch_document_assets(document_id)
    content = document["content"] or ""
    linked_document_ids = extract_linked_document_ids(content, document_id, parse_int=parse_int)
    linked_documents = provider.documents.fetch_documents_by_ids(linked_document_ids)
    linked_documents_by_id = {item["id"]: dict(item) for item in linked_documents}

    return {
        "document": dict(document),
        "related_tasks": serialize_rows(related_tasks),
        "tags": list(tags),
        "assets": serialize_rows(assets),
        "linked_documents": [
            linked_documents_by_id[linked_document_id]
            for linked_document_id in linked_document_ids
            if linked_document_id in linked_documents_by_id
        ],
        "rendered_content": str(markdown_to_html(content)),
        "word_count": len(content.split()),
        "heading_count": sum(1 for line in content.splitlines() if line.lstrip().startswith("#")),
    }


@router.post("")
async def create_document_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    data = _document_form_payload(payload)
    errors = _validate_document_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    folder_id = _resolve_document_folder_id(provider, data)
    document_id = provider.documents.create_document(data, folder_id)
    if data["asset_draft_key"]:
        provider.documents.assign_draft_assets(document_id, data["asset_draft_key"])
    provider.documents.sync_document_tags(document_id, data["tags"])
    provider.documents.sync_task_documents(document_id, data["related_task_ids"])
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "document_id": document_id,
        "redirect_path": f"/documents/{document_id}",
    }


@router.post("/{document_id}")
async def update_document_api(
    document_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    existing_document, _related_tasks, _tags = provider.documents.fetch_document_with_relations(
        document_id
    )
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document not found")

    data = _document_form_payload(payload)
    errors = _validate_document_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    folder_id = _resolve_document_folder_id(provider, data)
    provider.documents.update_document(document_id, data, folder_id)
    provider.documents.sync_document_tags(document_id, data["tags"])
    provider.documents.sync_task_documents(document_id, data["related_task_ids"])
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "document_id": document_id,
        "redirect_path": f"/documents/{document_id}",
    }


@router.delete("/{document_id}")
async def delete_document_api(
    document_id: int,
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    existing_document, _related_tasks, _tags = provider.documents.fetch_document_with_relations(
        document_id
    )
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document not found")

    assets = provider.documents.fetch_document_assets(document_id)
    for asset in assets:
        delete_object_with_config(
            settings.to_config_mapping(),
            dict(asset).get("object_key") or "",
        )
    provider.documents.delete_document(document_id)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "deleted": True,
        "redirect_path": "/documents",
    }


@router.post("/bulk")
async def bulk_documents_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    action = str(payload.get("action") or "").strip()
    document_ids = _normalize_document_ids(payload.get("document_ids") or [])

    if not document_ids:
        raise HTTPException(status_code=400, detail="처리할 문서를 선택해주세요.")

    documents = provider.documents.fetch_documents_by_ids(document_ids)
    existing_ids = sorted({int(document["id"]) for document in documents})
    if not existing_ids:
        raise HTTPException(status_code=404, detail="선택한 문서를 찾을 수 없습니다.")

    if action == "hide":
        updated_count = provider.documents.bulk_set_hidden(existing_ids, 1)
        if sqlite_db is not None:
            sqlite_db.commit()
        return {
            "updated": True,
            "action": action,
            "document_ids": existing_ids,
            "updated_count": updated_count,
        }

    if action == "unhide":
        updated_count = provider.documents.bulk_set_hidden(existing_ids, 0)
        if sqlite_db is not None:
            sqlite_db.commit()
        return {
            "updated": True,
            "action": action,
            "document_ids": existing_ids,
            "updated_count": updated_count,
        }

    if action == "delete":
        deleted_ids: list[int] = []
        for document_id in existing_ids:
            assets = provider.documents.fetch_document_assets(document_id)
            for asset in assets:
                delete_object_with_config(
                    settings.to_config_mapping(),
                    str(dict(asset).get("object_key") or ""),
                )
            provider.documents.delete_document(document_id)
            deleted_ids.append(document_id)
        if sqlite_db is not None:
            sqlite_db.commit()
        return {
            "deleted": True,
            "action": action,
            "document_ids": deleted_ids,
            "deleted_count": len(deleted_ids),
        }

    raise HTTPException(status_code=400, detail="지원하지 않는 일괄 처리입니다.")


@router.delete("/{document_id}/assets/{asset_id}")
async def delete_document_asset_api(
    document_id: int,
    asset_id: int,
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    existing_document, _related_tasks, _tags = provider.documents.fetch_document_with_relations(
        document_id
    )
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document not found")

    asset = provider.documents.fetch_document_asset(asset_id)
    if not asset or int(asset["document_id"] or 0) != document_id:
        raise HTTPException(status_code=404, detail="Document asset not found")

    delete_object_with_config(
        settings.to_config_mapping(),
        dict(asset).get("object_key") or "",
    )
    provider.documents.delete_document_asset(asset_id)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "deleted": True,
        "asset_id": asset_id,
        "document_id": document_id,
    }
