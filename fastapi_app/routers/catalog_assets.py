from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

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
SOURCE_PROVIDER = "external_catalog"
CATEGORY_LABELS = {"hair": "헤어", "face": "성형"}


class CatalogResourceIdRequest(BaseModel):
    resource_id: str = Field(min_length=32, max_length=32)


class CatalogAssetImportRequest(CatalogResourceIdRequest):
    add_to_avatar_catalog: bool = False
    gender: Literal["male", "female"] | None = None


class CatalogDocumentAssetRequest(CatalogResourceIdRequest):
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
        "tags": f"External Asset Catalog,{category_label},resource-id",
        "status": ASSET_STATUSES[0],
        "is_hidden": 0,
        "created_by": None,
        "notes": f"외부 카탈로그에서 가져온 에셋입니다.\nResource ID: {resource_id}",
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
        return existing, False, None

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
            logger.exception("Failed to roll back catalog asset object %s", stored["object_key"])
        raise
    asset = provider.assets.fetch_asset(asset_id)
    return asset, True, item


def _avatar_catalog_records(item, *, gender: str, master_resource_id: str, existing_group=None):
    existing = dict(existing_group) if existing_group is not None else {}
    variants = list(item.get("variants") or [])
    if not variants:
        variants = [
            {
                "resource_id": item["resource_id"],
                "name": item.get("name") or item["resource_id"],
                "dname": item.get("dname") or "",
                "color_hex": item.get("color_hex") or "",
                "thumbnail_url": item["thumbnail_url"],
            }
        ]
    master_variant = next(
        (variant for variant in variants if variant["resource_id"] == master_resource_id),
        None,
    )
    return [
        {
            "asset_type": item["category"],
            "gender": gender,
            "name": existing.get("name") or item.get("name") or master_resource_id,
            "source_index": int(existing.get("source_index") or 0),
            "availability": existing.get("availability") or "외부 카탈로그",
            "match_status": existing.get("match_status") or "검색 추가",
            "series": existing.get("series") or "",
            "confidence": existing.get("confidence") or "",
            "master_resource_id": master_resource_id,
            "group_id": item.get("group_id") or "",
            "group_size": len(variants),
            "master_color_hex": (
                existing.get("master_color_hex")
                or (master_variant or {}).get("color_hex")
                or ""
            ),
            "master_is_group_canonical": (
                existing.get("master_is_group_canonical")
                if existing
                else item.get("group_canonical") if item["resource_id"] == master_resource_id else False
            ),
            "variant_resource_id": variant["resource_id"],
            "thumbnail_url": variant["thumbnail_url"],
            "hex_code": variant.get("color_hex") or "",
            "variant_name": variant.get("name") or variant["resource_id"],
            "dname": variant.get("dname") or "",
        }
        for variant in variants
    ]


def _sync_avatar_catalog(*, item, gender: str, provider):
    category = item.get("category") or ""
    if category not in CATEGORY_LABELS:
        raise CatalogAssetError("헤어 또는 성형 에셋만 아바타 카탈로그에 추가할 수 있습니다.")
    existing_group = provider.avatar_assets.fetch_catalog_group(
        asset_type=category,
        gender=gender,
        group_id=item.get("group_id") or "",
    )
    master_resource_id = (
        existing_group["master_resource_id"] if existing_group is not None else item["resource_id"]
    )
    records = _avatar_catalog_records(
        item,
        gender=gender,
        master_resource_id=master_resource_id,
        existing_group=existing_group,
    )
    result = provider.avatar_assets.replace_catalog(records, replace=False)
    return {
        "gender": gender,
        "asset_type": category,
        "group_id": item.get("group_id") or "",
        **result,
    }


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
        asset, created, source_item = await _import_asset(
            resource_id=payload.resource_id,
            provider=provider,
            settings=settings,
        )
        catalog_result = None
        if payload.add_to_avatar_catalog:
            if payload.gender is None:
                raise CatalogAssetError("아바타 카탈로그에 추가하려면 성별을 선택해주세요.")
            if source_item is None:
                source_item = await asyncio.to_thread(fetch_catalog_asset, payload.resource_id)
            catalog_result = _sync_avatar_catalog(
                item=source_item,
                gender=payload.gender,
                provider=provider,
            )
    except CatalogAssetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if sqlite_db is not None:
        sqlite_db.commit()
    return {
        "asset": _serialize(asset),
        "created": created,
        "avatar_catalog": catalog_result,
    }


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
        asset, created, _source_item = await _import_asset(
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
