from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from app.constants import ASSET_STATUSES
from app.catalog_assets import (
    CatalogAssetError,
    download_catalog_thumbnail_png,
    fetch_catalog_asset,
    search_catalog_assets,
    validate_resource_id,
)
from app.storage import delete_object_with_config, upload_file_from_stream

from ..dependencies import get_repository_provider, get_runtime_sqlite_db, get_settings


router = APIRouter(prefix="/api/catalog-assets", tags=["catalog-assets"])
logger = logging.getLogger(__name__)
SOURCE_PROVIDER = "studiostory_worlds"
CATEGORY_LABELS = {"hair": "헤어", "face": "성형"}


class CatalogAssetImportRequest(BaseModel):
    resource_id: str = Field(min_length=32, max_length=32)


class CatalogDocumentAssetRequest(CatalogAssetImportRequest):
    document_id: int | None = Field(default=None, ge=1)
    draft_key: str | None = Field(default=None, max_length=100)
    alt: str = Field(default="", max_length=200)


def _serialize(row) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def _asset_data(item, uploaded):
    resource_id = item["resource_id"]
    category = item["category"]
    category_label = CATEGORY_LABELS.get(category, category or "기타")
    return {
        "title": item["name"] or resource_id,
        "asset_type": "sprite",
        "category": f"External Asset Catalog/{category_label}",
        "tags": f"External Asset Catalog,{category_label},RESOURCE_ID",
        "status": ASSET_STATUSES[0],
        "is_hidden": 0,
        "created_by": None,
        "notes": f"External Asset Catalog Resource Search에서 가져온 에셋입니다.\nRESOURCE_ID: {resource_id}",
        "file_name": uploaded["filename"],
        "original_filename": uploaded["filename"],
        "object_key": uploaded["object_key"],
        "url": uploaded["url"],
        "content_type": uploaded["content_type"],
        "size": int(uploaded["size"]),
        "checksum": uploaded["checksum"],
        "source_provider": SOURCE_PROVIDER,
        "source_resource_id": resource_id,
        "source_url": item["thumbnail_url"],
    }


def _download_and_store_asset(*, resource_id: str, settings):
    item = fetch_catalog_asset(resource_id)
    downloaded = download_catalog_thumbnail_png(
        resource_id,
        max_download_size=settings.max_content_length,
    )
    stored = upload_file_from_stream(
        settings.to_config_mapping(),
        filename=downloaded["filename"],
        stream=downloaded["stream"],
        content_type=downloaded["content_type"],
        folder="assets/catalog",
        max_size=settings.max_content_length,
    )
    return item, downloaded, stored


async def _import_asset(*, resource_id: str, provider, settings):
    normalized_resource_id = validate_resource_id(resource_id)
    existing = provider.assets.fetch_asset_by_source(SOURCE_PROVIDER, normalized_resource_id)
    if existing:
        return existing, False

    item, downloaded, stored = await asyncio.to_thread(
        _download_and_store_asset,
        resource_id=normalized_resource_id,
        settings=settings,
    )
    uploaded = {**downloaded, **stored}
    data = _asset_data(item, uploaded)
    try:
        asset_id = provider.assets.create_asset(data)
    except Exception:
        try:
            await asyncio.to_thread(
                delete_object_with_config,
                settings.to_config_mapping(),
                stored["object_key"],
            )
        except Exception:
            logger.exception("Failed to roll back CATALOG asset object %s", stored["object_key"])
        raise
    asset = provider.assets.fetch_asset(asset_id)
    return asset, True


def _markdown_alt(value: str, fallback: str) -> str:
    return (value.strip() or fallback).replace("\n", " ").replace("]", "\\]")


@router.get("/search")
async def search_assets(q: str = "", limit: int = 12, offset: int = 0):
    try:
        return await asyncio.to_thread(search_catalog_assets, q, limit=limit, offset=offset)
    except CatalogAssetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import")
async def import_asset(
    payload: CatalogAssetImportRequest = Body(...),
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    try:
        asset, created = await _import_asset(
            resource_id=payload.resource_id,
            provider=provider,
            settings=settings,
        )
    except CatalogAssetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if sqlite_db is not None:
        sqlite_db.commit()
    return {"asset": _serialize(asset), "created": created}


@router.post("/insert-document")
async def insert_document_asset(
    payload: CatalogDocumentAssetRequest = Body(...),
    provider=Depends(get_repository_provider),
    settings=Depends(get_settings),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    draft_key = (payload.draft_key or "").strip() or None
    if payload.document_id is None and draft_key is None:
        raise HTTPException(status_code=400, detail="document_id 또는 draft_key가 필요합니다.")
    if payload.document_id is not None:
        document, _tasks, _tags = provider.documents.fetch_document_with_relations(
            payload.document_id
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

    try:
        asset, created = await _import_asset(
            resource_id=payload.resource_id,
            provider=provider,
            settings=settings,
        )
    except CatalogAssetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if sqlite_db is not None:
        sqlite_db.commit()

    alt = _markdown_alt(payload.alt, str(asset["title"] or payload.resource_id))
    document_asset_id = provider.documents.create_linked_document_asset(
        document_id=payload.document_id,
        draft_key=draft_key,
        linked_asset_id=int(asset["id"]),
        alt_text=alt,
    )
    if sqlite_db is not None:
        sqlite_db.commit()
    image = provider.documents.fetch_document_asset(document_asset_id)
    return {
        "asset": _serialize(asset),
        "image": _serialize(image),
        "created": created,
        "markdown": f"![{alt}]({asset['url']})",
    }
