from __future__ import annotations

from io import BytesIO
import json
import re
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, UnidentifiedImageError


SEARCH_URL = "https://catalog.example.com/api/v3/search/resources"
THUMBNAIL_URL_TEMPLATE = (
    "https://catalog.example.com/"
    "api/v3/resources/thumbnail/{resource_id}.webp"
)
RESOURCE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
MAX_SEARCH_LIMIT = 30


class CatalogAssetError(RuntimeError):
    pass


def validate_resource_id(resource_id: str) -> str:
    normalized = str(resource_id or "").strip().lower()
    if not RESOURCE_ID_PATTERN.fullmatch(normalized):
        raise CatalogAssetError("RESOURCE_ID는 32자리 소문자 16진수여야 합니다.")
    return normalized


def build_thumbnail_url(resource_id: str) -> str:
    return THUMBNAIL_URL_TEMPLATE.format(resource_id=validate_resource_id(resource_id))


def _display_name(names: Any) -> str:
    if not isinstance(names, Mapping):
        return ""
    for locale in ("ko", "en"):
        values = names.get(locale)
        if isinstance(values, list) and values:
            return str(values[0]).strip()
    return ""


def _search_request(query: str, *, limit: int, offset: int, timeout: float) -> dict[str, Any]:
    request = Request(
        SEARCH_URL,
        data=json.dumps(
            {
                "query": query,
                "topK": limit,
                "offset": offset,
                "resourceTypeFilter": ["avataritem"],
            }
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "agentic-product-studio/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise CatalogAssetError(f"External Asset Catalog 검색 요청에 실패했습니다: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise CatalogAssetError("External Asset Catalog가 올바르지 않은 검색 응답을 반환했습니다.")
    return payload


def _normalize_variant(raw: Mapping[str, Any]) -> dict[str, str]:
    resource_id = validate_resource_id(str(raw.get("resource_id") or ""))
    return {
        "resource_id": resource_id,
        "name": _display_name(raw.get("names")) or str(raw.get("dname") or resource_id),
        "dname": str(raw.get("dname") or ""),
        "color_hex": str(raw.get("color") or ""),
        "thumbnail_url": build_thumbnail_url(resource_id),
    }


def _normalize_result(raw: Mapping[str, Any]) -> dict[str, Any]:
    resource_id = validate_resource_id(str(raw.get("id") or ""))
    payload = raw.get("payload") if isinstance(raw.get("payload"), Mapping) else {}
    raw_members = payload.get("group_members")
    if isinstance(raw_members, list) and raw_members:
        variants = [
            _normalize_variant(member)
            for member in raw_members
            if isinstance(member, Mapping)
        ]
    else:
        variants = [
            _normalize_variant(
                {
                    "resource_id": resource_id,
                    "names": raw.get("names"),
                    "dname": raw.get("dname"),
                    "color": payload.get("color_hex"),
                }
            )
        ]
    return {
        "resource_id": resource_id,
        "name": _display_name(raw.get("names")) or str(raw.get("dname") or resource_id),
        "dname": str(raw.get("dname") or ""),
        "category": str(raw.get("category") or ""),
        "resource_type": str(raw.get("type") or ""),
        "color_hex": str(payload.get("color_hex") or ""),
        "group_id": str(payload.get("group_id") or ""),
        "group_canonical": str(payload.get("group_canonical") or "").lower()
        in {"1", "true", "yes", "on"},
        "thumbnail_url": build_thumbnail_url(resource_id),
        "variants": variants,
    }


def search_catalog_assets(query: str, *, limit: int = 12, offset: int = 0, timeout: float = 15.0):
    normalized_query = str(query or "").strip()
    if not normalized_query:
        raise CatalogAssetError("검색어를 입력해주세요.")
    if len(normalized_query) > 100:
        raise CatalogAssetError("검색어는 100자 이하여야 합니다.")
    normalized_limit = max(1, min(int(limit), MAX_SEARCH_LIMIT))
    normalized_offset = max(0, int(offset))
    payload = _search_request(
        normalized_query,
        limit=normalized_limit,
        offset=normalized_offset,
        timeout=timeout,
    )

    items = []
    seen_groups = set()
    for raw in payload["results"]:
        if not isinstance(raw, Mapping):
            continue
        item = _normalize_result(raw)
        group_key = item["group_id"] or item["resource_id"]
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)
        items.append(item)

    next_offset = payload.get("nextOffset")
    return {
        "query": normalized_query,
        "items": items,
        "pagination": {
            "limit": normalized_limit,
            "offset": normalized_offset,
            "next_offset": int(next_offset) if isinstance(next_offset, int) else None,
            "has_more": isinstance(next_offset, int) and next_offset > normalized_offset,
        },
    }


def fetch_catalog_asset(resource_id: str, *, timeout: float = 15.0):
    normalized_resource_id = validate_resource_id(resource_id)
    payload = _search_request(normalized_resource_id, limit=1, offset=0, timeout=timeout)
    results = payload.get("results") or []
    if payload.get("exactMatch") is not True or len(results) != 1:
        raise CatalogAssetError("해당 RESOURCE_ID의 External Asset Catalog 에셋을 찾지 못했습니다.")
    item = _normalize_result(results[0])
    if item["resource_id"] != normalized_resource_id:
        raise CatalogAssetError("External Asset Catalog 검색 결과의 RESOURCE_ID가 요청과 일치하지 않습니다.")
    return item


def download_catalog_thumbnail_png(
    resource_id: str,
    *,
    max_download_size: int,
    timeout: float = 30.0,
):
    normalized_resource_id = validate_resource_id(resource_id)
    source_url = build_thumbnail_url(normalized_resource_id)
    request = Request(
        source_url,
        headers={"Accept": "image/webp", "User-Agent": "agentic-product-studio/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if content_type != "image/webp":
                raise CatalogAssetError(
                    f"External Asset Catalog 썸네일 형식이 WebP가 아닙니다: {content_type or 'unknown'}"
                )
            source = response.read(max_download_size + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise CatalogAssetError(f"External Asset Catalog 썸네일 다운로드에 실패했습니다: {exc}") from exc
    if len(source) > max_download_size:
        raise CatalogAssetError("External Asset Catalog 썸네일이 허용 크기를 초과했습니다.")

    output = BytesIO()
    try:
        with Image.open(BytesIO(source)) as image:
            if image.format != "WEBP":
                raise CatalogAssetError("다운로드한 썸네일이 올바른 WebP 파일이 아닙니다.")
            image.load()
            image.convert("RGBA").save(output, format="PNG", optimize=True)
    except (OSError, UnidentifiedImageError) as exc:
        raise CatalogAssetError(f"External Asset Catalog 썸네일 변환에 실패했습니다: {exc}") from exc
    output.seek(0)
    return {
        "stream": output,
        "filename": f"{normalized_resource_id}.png",
        "content_type": "image/png",
        "source_url": source_url,
    }
