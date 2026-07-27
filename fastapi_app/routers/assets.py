from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Body, File, Form, UploadFile
from fastapi.responses import Response

from app.constants import ASSET_STATUSES
from app.storage import (
    delete_object_with_config,
    read_object_bytes_with_config,
    upload_file_from_stream,
)
from app.utils import build_pagination, parse_int

from ..dependencies import get_repository_provider, get_runtime_sqlite_db, get_settings
from ..helpers import (
    PER_PAGE_OPTIONS,
    asset_group_payload,
    asset_type_options,
    serialize_rows,
)


router = APIRouter(prefix="/api/assets", tags=["assets"])


def _asset_form_payload(payload, *, uploaded=None, existing=None):
    existing_data = dict(existing) if existing else {}
    return {
        "title": (payload.get("title") or "").strip(),
        "asset_type": (payload.get("asset_type") or "").strip(),
        "category": (payload.get("category") or "").strip(),
        "tags": (payload.get("tags") or "").strip(),
        "status": (payload.get("status") or ASSET_STATUSES[0]).strip(),
        "is_hidden": 1 if payload.get("is_hidden") else 0,
        "created_by": payload.get("created_by") or None,
        "notes": (payload.get("notes") or "").strip(),
        "file_name": uploaded["file_name"] if uploaded else existing_data.get("file_name", ""),
        "original_filename": uploaded["original_filename"] if uploaded else existing_data.get(
            "original_filename", ""
        ),
        "object_key": uploaded["object_key"] if uploaded else existing_data.get("object_key", ""),
        "url": uploaded["url"] if uploaded else existing_data.get("url", ""),
        "content_type": uploaded["content_type"] if uploaded else existing_data.get(
            "content_type", ""
        ),
        "size": int(uploaded["size"]) if uploaded else int(existing_data.get("size") or 0),
        "checksum": uploaded["checksum"] if uploaded else existing_data.get("checksum", ""),
    }


def _validate_asset_payload(data, *, require_file: bool):
    errors = []
    if not data["title"]:
        errors.append("Asset 제목은 필수입니다.")
    if data["status"] not in ASSET_STATUSES:
        errors.append("유효하지 않은 Asset 상태입니다.")
    if require_file and not data["object_key"]:
        errors.append("업로드할 파일은 필수입니다.")
    if data["created_by"] and not str(data["created_by"]).isdigit():
        errors.append("유효하지 않은 등록자입니다.")
    return errors


def _unique_download_name(filename: str, used_names: set[str]) -> str:
    normalized = (filename or "").strip() or "asset"
    if normalized not in used_names:
        used_names.add(normalized)
        return normalized

    stem, dot, suffix = normalized.rpartition(".")
    if not dot:
        stem = normalized
        suffix = ""

    index = 2
    while True:
        candidate = f"{stem} ({index})"
        if suffix:
            candidate = f"{candidate}.{suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        index += 1


@router.get("")
async def assets_list(
    q: str = "",
    asset_type: str = "",
    category: str = "",
    status: str = "",
    tag: str = "",
    updated_since: str = "",
    include_hidden: str = "",
    page: int = 1,
    per_page: int = 20,
    provider=Depends(get_repository_provider),
):
    normalized_include_hidden = str(include_hidden).strip().lower() in {"1", "true", "yes", "on"}
    normalized_page = parse_int(page, default=1, minimum=1)
    normalized_per_page = parse_int(per_page, default=20, allowed=set(PER_PAGE_OPTIONS))

    total_count, assets = provider.assets.list_assets(
        search=q.strip(),
        asset_type=asset_type.strip(),
        category=category.strip(),
        status=status.strip(),
        tag=tag.strip(),
        include_hidden=normalized_include_hidden,
        updated_since=updated_since.strip(),
        limit=normalized_per_page,
        offset=max((normalized_page - 1) * normalized_per_page, 0),
    )
    pagination = build_pagination(normalized_page, normalized_per_page, total_count)

    return {
        "assets": serialize_rows(assets),
        "statuses": list(ASSET_STATUSES),
        "asset_type_options": asset_type_options(provider),
        "category_options": serialize_rows(
            provider.assets.fetch_category_options(include_hidden=normalized_include_hidden)
        ),
        "group_browser": asset_group_payload(provider, include_hidden=normalized_include_hidden),
        "tag_options": serialize_rows(provider.assets.fetch_tag_options()),
        "pagination": pagination,
        "per_page_options": list(PER_PAGE_OPTIONS),
        "filters": {
            "q": q.strip(),
            "asset_type": asset_type.strip(),
            "category": category.strip(),
            "status": status.strip(),
            "tag": tag.strip(),
            "updated_since": updated_since.strip(),
            "include_hidden": normalized_include_hidden,
        },
    }


@router.get("/editor")
async def asset_editor_bootstrap(
    asset_id: int = Query(default=0),
    provider=Depends(get_repository_provider),
):
    normalized_asset_id = parse_int(asset_id, default=0, minimum=0)
    asset = None
    tags = []
    if normalized_asset_id:
        asset, tags = provider.assets.fetch_asset_with_tags(normalized_asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

    return {
        "asset": dict(asset) if asset else None,
        "tags": list(tags),
        "statuses": list(ASSET_STATUSES),
        "asset_type_options": asset_type_options(provider),
        "members": serialize_rows(provider.common.fetch_active_members()),
        "group_browser": asset_group_payload(provider, include_hidden=True),
    }


@router.get("/groups")
async def asset_group_list_api(
    include_hidden: str = "",
    provider=Depends(get_repository_provider),
):
    normalized_include_hidden = str(include_hidden).strip().lower() in {"1", "true", "yes", "on"}
    return asset_group_payload(provider, include_hidden=normalized_include_hidden)


@router.get("/{asset_id}")
async def asset_detail(asset_id: int, provider=Depends(get_repository_provider)):
    asset, tags = provider.assets.fetch_asset_with_tags(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {
        "asset": dict(asset),
        "tags": list(tags),
        "is_image": str(dict(asset).get("content_type") or "").startswith("image/"),
    }


@router.get("/{asset_id}/download")
async def asset_download(
    asset_id: int,
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
):
    asset = provider.assets.fetch_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset_data = dict(asset)
    object_key = str(asset_data.get("object_key") or "").strip()
    download_name = (
        str(asset_data.get("original_filename") or "").strip()
        or str(asset_data.get("file_name") or "").strip()
        or f"asset-{asset_id}"
    )
    content_type = str(asset_data.get("content_type") or "").strip() or None

    try:
        body, detected_content_type = read_object_bytes_with_config(
            settings.to_config_mapping(),
            object_key,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Asset file not found")

    headers = {"Content-Disposition": f'attachment; filename="{download_name}"'}
    return Response(
        content=body,
        media_type=content_type or detected_content_type or "application/octet-stream",
        headers=headers,
    )


@router.get("/download")
async def asset_bulk_download(
    asset_ids: list[str] = Query(default_factory=list),
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
):
    normalized_ids: list[int] = []
    seen_ids: set[int] = set()
    for raw_id in asset_ids:
        asset_id = parse_int(raw_id, default=0, minimum=1)
        if asset_id and asset_id not in seen_ids:
            seen_ids.add(asset_id)
            normalized_ids.append(asset_id)

    if not normalized_ids:
        raise HTTPException(status_code=400, detail="다운로드할 Asset을 선택해주세요.")

    assets = []
    for asset_id in normalized_ids:
        asset = provider.assets.fetch_asset(asset_id)
        if asset:
            assets.append(dict(asset))

    if not assets:
        raise HTTPException(status_code=404, detail="다운로드할 Asset을 찾지 못했습니다.")

    archive_buffer = BytesIO()
    used_names: set[str] = set()
    added_count = 0
    with ZipFile(archive_buffer, "w", compression=ZIP_DEFLATED) as archive:
        for asset in assets:
            object_key = str(asset.get("object_key") or "").strip()
            if not object_key:
                continue

            try:
                body, _content_type = read_object_bytes_with_config(
                    settings.to_config_mapping(),
                    object_key,
                )
            except FileNotFoundError:
                continue

            download_name = _unique_download_name(
                str(asset.get("original_filename") or "").strip()
                or str(asset.get("file_name") or "").strip()
                or f"asset-{asset['id']}",
                used_names,
            )
            archive.writestr(download_name, body)
            added_count += 1

    if not added_count:
        raise HTTPException(status_code=404, detail="다운로드 가능한 Asset 파일을 찾지 못했습니다.")

    archive_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    headers = {"Content-Disposition": f'attachment; filename="assets-{timestamp}.zip"'}
    return Response(
        content=archive_buffer.getvalue(),
        media_type="application/zip",
        headers=headers,
    )


@router.post("/groups")
async def create_asset_group_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    parent_path = str(payload.get("parent_path") or "").strip()
    name = str(payload.get("name") or "").strip()
    combined = "/".join(part for part in [parent_path, name] if part)
    if not name:
        raise HTTPException(status_code=400, detail="새 폴더 이름을 입력해주세요.")
    try:
        path = provider.assets.create_asset_group(combined)
        if sqlite_db is not None:
            sqlite_db.commit()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "path": path,
        "group_browser": asset_group_payload(provider, include_hidden=True),
    }


@router.post("/groups/rename")
async def rename_asset_group_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    path = str(payload.get("path") or "").strip()
    new_name = str(payload.get("new_name") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="변경할 폴더 이름을 입력해주세요.")
    try:
        renamed_path = provider.assets.rename_asset_group(path, new_name)
        if sqlite_db is not None:
            sqlite_db.commit()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "path": renamed_path,
        "group_browser": asset_group_payload(provider, include_hidden=True),
    }


@router.delete("/groups")
async def delete_asset_group_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    path = str(payload.get("path") or "").strip()
    try:
        provider.assets.delete_asset_group(path)
        if sqlite_db is not None:
            sqlite_db.commit()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "deleted": True,
        "group_browser": asset_group_payload(provider, include_hidden=True),
    }


@router.post("")
async def create_asset_api(
    title: str = Form(default=""),
    asset_type: str = Form(default=""),
    category: str = Form(default=""),
    tags: str = Form(default=""),
    status: str = Form(default=ASSET_STATUSES[0]),
    is_hidden: str = Form(default=""),
    created_by: str = Form(default=""),
    notes: str = Form(default=""),
    file: UploadFile | None = File(default=None),
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    uploaded = None
    if file and file.filename:
        stored = upload_file_from_stream(
            settings.to_config_mapping(),
            filename=file.filename,
            stream=file.file,
            content_type=file.content_type,
            folder="assets",
        )
        uploaded = {
            **stored,
            "file_name": file.filename,
            "original_filename": file.filename,
        }

    payload = {
        "title": title,
        "asset_type": asset_type,
        "category": category,
        "tags": tags,
        "status": status,
        "is_hidden": is_hidden in {"1", "true", "yes", "on"},
        "created_by": created_by or None,
        "notes": notes,
    }
    data = _asset_form_payload(payload, uploaded=uploaded)
    errors = _validate_asset_payload(data, require_file=True)
    if errors:
        if uploaded:
            delete_object_with_config(settings.to_config_mapping(), uploaded["object_key"])
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    try:
        asset_id = provider.assets.create_asset(data)
        if sqlite_db is not None:
            sqlite_db.commit()
    except Exception:
        if uploaded:
            delete_object_with_config(settings.to_config_mapping(), uploaded["object_key"])
        raise
    return {"asset_id": asset_id, "redirect_path": f"/assets/{asset_id}"}


@router.post("/{asset_id}")
async def update_asset_api(
    asset_id: int,
    title: str = Form(default=""),
    asset_type: str = Form(default=""),
    category: str = Form(default=""),
    tags: str = Form(default=""),
    status: str = Form(default=ASSET_STATUSES[0]),
    is_hidden: str = Form(default=""),
    created_by: str = Form(default=""),
    notes: str = Form(default=""),
    file: UploadFile | None = File(default=None),
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    existing = provider.assets.fetch_asset(asset_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")

    uploaded = None
    if file and file.filename:
        stored = upload_file_from_stream(
            settings.to_config_mapping(),
            filename=file.filename,
            stream=file.file,
            content_type=file.content_type,
            folder="assets",
        )
        uploaded = {
            **stored,
            "file_name": file.filename,
            "original_filename": file.filename,
        }

    payload = {
        "title": title,
        "asset_type": asset_type,
        "category": category,
        "tags": tags,
        "status": status,
        "is_hidden": is_hidden in {"1", "true", "yes", "on"},
        "created_by": created_by or None,
        "notes": notes,
    }
    data = _asset_form_payload(payload, uploaded=uploaded, existing=existing)
    errors = _validate_asset_payload(data, require_file=False)
    if errors:
        if uploaded:
            delete_object_with_config(settings.to_config_mapping(), uploaded["object_key"])
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    try:
        provider.assets.update_asset(asset_id, data)
        if sqlite_db is not None:
            sqlite_db.commit()
    except Exception:
        if uploaded:
            delete_object_with_config(settings.to_config_mapping(), uploaded["object_key"])
        raise
    existing_object_key = dict(existing).get("object_key") or ""
    if uploaded and existing_object_key and existing_object_key != data["object_key"]:
        delete_object_with_config(settings.to_config_mapping(), existing_object_key)
    return {"asset_id": asset_id, "redirect_path": f"/assets/{asset_id}"}


@router.delete("/{asset_id}")
async def delete_asset_api(
    asset_id: int,
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    existing = provider.assets.fetch_asset(asset_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")
    provider.assets.delete_asset(asset_id)
    if sqlite_db is not None:
        sqlite_db.commit()
    delete_object_with_config(settings.to_config_mapping(), dict(existing).get("object_key") or "")
    return {"deleted": True, "redirect_path": "/assets"}
