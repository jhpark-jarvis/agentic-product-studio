from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_repository_provider


router = APIRouter(prefix="/api/avatar-assets", tags=["avatar-assets"])


@router.get("")
async def avatar_catalog_list(
    q: str = "",
    asset_type: str = "",
    gender: str = "",
    provider=Depends(get_repository_provider),
):
    return {
        "assets": provider.avatar_assets.fetch_catalog(
            search=q.strip(),
            asset_type=asset_type.strip(),
            gender=gender.strip(),
        ),
        "summary": provider.avatar_assets.fetch_catalog_summary(),
        "filters": {
            "q": q.strip(),
            "asset_type": asset_type.strip(),
            "gender": gender.strip(),
        },
    }
