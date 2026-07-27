from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.utils import parse_int

from ..dependencies import get_repository_provider, get_runtime_sqlite_db
from ..helpers import serialize_rows


router = APIRouter(prefix="/api/members", tags=["members"])


def _member_form_payload(payload):
    return {
        "name": (payload.get("name") or "").strip(),
        "role": (payload.get("role") or "").strip(),
        "part": (payload.get("part") or "").strip(),
        "contact": (payload.get("contact") or "").strip(),
        "is_active": 1 if payload.get("is_active") else 0,
    }


def _validate_member_payload(data):
    errors = []
    if not data["name"]:
        errors.append("팀원 이름은 필수입니다.")
    return errors


@router.get("")
async def members_list(provider=Depends(get_repository_provider)):
    members = provider.members.list_members()
    return {"members": serialize_rows(members)}


@router.get("/editor")
async def member_editor_bootstrap(
    member_id: int = Query(default=0),
    provider=Depends(get_repository_provider),
):
    normalized_member_id = parse_int(member_id, default=0, minimum=0)
    member = None
    if normalized_member_id:
        member = provider.members.fetch_member(normalized_member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
    return {"member": dict(member) if member else None}


@router.post("")
async def create_member_api(
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    data = _member_form_payload(payload)
    errors = _validate_member_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    member_id = provider.members.create_member(data)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "member_id": member_id,
        "redirect_path": "/members",
    }


@router.post("/{member_id}")
async def update_member_api(
    member_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    member = provider.members.fetch_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    data = _member_form_payload(payload)
    errors = _validate_member_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"error": errors[0], "errors": errors})

    provider.members.update_member(member_id, data)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {
        "member_id": member_id,
        "redirect_path": "/members",
    }


@router.delete("/{member_id}")
async def delete_member_api(
    member_id: int,
    provider=Depends(get_repository_provider),
    sqlite_db=Depends(get_runtime_sqlite_db),
):
    member = provider.members.fetch_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    provider.members.delete_member(member_id)
    if sqlite_db is not None:
        sqlite_db.commit()

    return {"deleted": True, "redirect_path": "/members"}
