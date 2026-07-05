from workers import WorkerEntrypoint

from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import asgi

from d1_queries import (
    create_document_folder_record,
    create_document_record,
    create_member_record,
    create_schedule_record,
    create_wbs_record,
    delete_document_asset_record,
    delete_document_record,
    delete_member_record,
    delete_schedule_record,
    delete_wbs_record,
    fetch_common_options_payload,
    fetch_dashboard_payload,
    fetch_document_folders_payload,
    fetch_member_detail_payload,
    fetch_members_payload,
    fetch_document_detail_payload,
    fetch_documents_payload,
    fetch_document_asset_payload,
    fetch_document_assets_payload,
    fetch_schedule_detail_payload,
    fetch_schedules_payload,
    fetch_wbs_payload,
    sync_document_tags,
    sync_document_task_links,
    sync_wbs_task_documents,
    update_document_folder_record,
    update_document_record,
    update_member_record,
    update_schedule_record,
    update_wbs_record,
)
from models import (
    DOCUMENT_TYPES,
    SCHEDULE_TYPES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    WBS_PLATFORM_OPTIONS,
    DocumentFolderPayload,
    DocumentPayload,
    MemberPayload,
    SchedulePayload,
    WbsPayload,
)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)


app = FastAPI(
    title="Agentic Product Studio Cloudflare Worker",
    version="0.1.0",
)


def _parse_iso_date(value: str | None):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _has_binding(env, name: str) -> bool:
    return getattr(env, name, None) is not None


async def _resolve_folder_id(env, *, doc_type: str, folder_id: int | None, new_folder_name: str):
    if new_folder_name.strip():
        return await create_document_folder_record(
            env,
            doc_type=doc_type,
            folder_name=new_folder_name.strip(),
        )
    return folder_id


async def _delete_r2_object_if_present(env, object_key: str | None):
    if not object_key:
        return
    bucket = getattr(env, "DOCUMENT_IMAGES", None)
    if bucket is None:
        return
    await bucket.delete(object_key)


@app.get("/")
async def root():
    return {
        "service": "agentic-product-studio-python-worker",
        "status": "bootstrap-ready",
        "message": "Cloudflare Python Worker scaffold is ready.",
        "next_step": "Port Flask routes and rendering flow into an ASGI-compatible runtime.",
    }


@app.get("/health")
async def health(request: Request):
    env = request.scope["env"]
    return {
        "ok": True,
        "service": "agentic-product-studio-python-worker",
        "has_db_binding": _has_binding(env, "DB"),
        "has_image_bucket_binding": _has_binding(env, "DOCUMENT_IMAGES"),
    }


@app.get("/api/runtime-summary")
async def runtime_summary(request: Request):
    env = request.scope["env"]

    summary = {
        "worker_runtime": "python-workers-beta",
        "bindings": {
            "db": _has_binding(env, "DB"),
            "document_images": _has_binding(env, "DOCUMENT_IMAGES"),
        },
    }

    if not _has_binding(env, "DB"):
        return summary

    try:
        table_list = await env.DB.prepare("PRAGMA table_list").run()
        summary["d1"] = {
            "connected": True,
            "table_list": table_list,
        }
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        summary["d1"] = {
            "connected": False,
            "error": str(exc),
        }

    return summary


@app.get("/api/dashboard-summary")
async def dashboard_summary(request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        result = await env.DB.prepare(
            """
            SELECT
                COUNT(*) AS total_tasks,
                SUM(CASE WHEN status IN ('진행중', '검토중') THEN 1 ELSE 0 END) AS in_progress_tasks,
                SUM(CASE WHEN status = '완료' THEN 1 ELSE 0 END) AS completed_tasks
            FROM wbs_tasks
            """
        ).run()
        return result
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to query dashboard summary from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/dashboard")
async def dashboard(request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        return await fetch_dashboard_payload(env)
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load dashboard payload from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/documents")
async def documents(
    request: Request,
    q: str = "",
    doc_type: str = "",
    tag: str = "",
    folder_id: str = "",
    limit: int = 20,
    offset: int = 0,
):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)

    try:
        return await fetch_documents_payload(
            env,
            search=q.strip(),
            doc_type=doc_type.strip(),
            tag=tag.strip(),
            folder_id=folder_id.strip(),
            limit=safe_limit,
            offset=safe_offset,
        )
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load documents payload from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/documents/{document_id}")
async def document_detail(document_id: int, request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        payload = await fetch_document_detail_payload(env, document_id)
        if payload is None:
            return JSONResponse({"error": "Document not found."}, status_code=404)
        return payload
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load document detail from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/document-folders")
async def document_folders(request: Request, doc_type: str | None = None):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        return await fetch_document_folders_payload(env, doc_type=doc_type.strip() if doc_type else None)
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load document folders from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/documents/{document_id}/assets")
async def document_assets(document_id: int, request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    document = await fetch_document_detail_payload(env, document_id)
    if not document:
        return JSONResponse({"error": "Document not found."}, status_code=404)

    try:
        return await fetch_document_assets_payload(env, document_id)
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load document assets from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/wbs")
async def wbs(
    request: Request,
    status: str = "",
    assignee_id: str = "",
    priority: str = "",
    platform: str = "",
):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        return await fetch_wbs_payload(
            env,
            status=status.strip(),
            assignee_id=assignee_id.strip(),
            priority=priority.strip(),
            platform=platform.strip(),
        )
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load WBS payload from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/members")
async def members(request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        return await fetch_members_payload(env)
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load members payload from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/members/{member_id}")
async def member_detail(member_id: int, request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        payload = await fetch_member_detail_payload(env, member_id)
        if payload is None:
            return JSONResponse({"error": "Member not found."}, status_code=404)
        return payload
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load member detail from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/schedules")
async def schedules(request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        return await fetch_schedules_payload(env)
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load schedules payload from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/schedules/{schedule_id}")
async def schedule_detail(schedule_id: int, request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        payload = await fetch_schedule_detail_payload(env, schedule_id)
        if payload is None:
            return JSONResponse({"error": "Schedule not found."}, status_code=404)
        return payload
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load schedule detail from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.get("/api/common/options")
async def common_options(request: Request, exclude_task_id: int | None = None):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    try:
        return await fetch_common_options_payload(env, exclude_task_id=exclude_task_id)
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse(
            {
                "error": "Failed to load common options payload from D1.",
                "detail": str(exc),
            },
            status_code=500,
        )


@app.post("/api/members")
async def create_member(request: Request, payload: MemberPayload):
    env = request.scope["env"]
    try:
        member_id = await create_member_record(
            env,
            name=payload.name.strip(),
            role=payload.role.strip(),
            part=payload.part.strip(),
            contact=payload.contact.strip(),
            is_active=1 if payload.is_active else 0,
        )
        return {"id": member_id, "message": "Member created."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to create member.", "detail": str(exc)}, status_code=500)


@app.put("/api/members/{member_id}")
async def update_member(member_id: int, request: Request, payload: MemberPayload):
    env = request.scope["env"]
    try:
        await update_member_record(
            env,
            member_id,
            name=payload.name.strip(),
            role=payload.role.strip(),
            part=payload.part.strip(),
            contact=payload.contact.strip(),
            is_active=1 if payload.is_active else 0,
        )
        return {"id": member_id, "message": "Member updated."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to update member.", "detail": str(exc)}, status_code=500)


@app.delete("/api/members/{member_id}")
async def delete_member(member_id: int, request: Request):
    env = request.scope["env"]
    try:
        await delete_member_record(env, member_id)
        return {"id": member_id, "message": "Member deleted."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to delete member.", "detail": str(exc)}, status_code=500)


@app.post("/api/schedules")
async def create_schedule(request: Request, payload: SchedulePayload):
    env = request.scope["env"]
    start = _parse_iso_date(payload.start_date)
    end = _parse_iso_date(payload.end_date)
    if not start or not end:
        return JSONResponse({"error": "Invalid schedule date format."}, status_code=400)
    if end < start:
        return JSONResponse({"error": "end_date cannot be earlier than start_date."}, status_code=400)
    if payload.schedule_type not in SCHEDULE_TYPES:
        return JSONResponse({"error": "Invalid schedule_type."}, status_code=400)

    try:
        schedule_id = await create_schedule_record(
            env,
            title=payload.title.strip(),
            description=payload.description.strip(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            assignee_id=payload.assignee_id,
            wbs_task_id=payload.wbs_task_id,
            schedule_type=payload.schedule_type,
        )
        return {"id": schedule_id, "message": "Schedule created."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to create schedule.", "detail": str(exc)}, status_code=500)


@app.put("/api/schedules/{schedule_id}")
async def update_schedule(schedule_id: int, request: Request, payload: SchedulePayload):
    env = request.scope["env"]
    start = _parse_iso_date(payload.start_date)
    end = _parse_iso_date(payload.end_date)
    if not start or not end:
        return JSONResponse({"error": "Invalid schedule date format."}, status_code=400)
    if end < start:
        return JSONResponse({"error": "end_date cannot be earlier than start_date."}, status_code=400)
    if payload.schedule_type not in SCHEDULE_TYPES:
        return JSONResponse({"error": "Invalid schedule_type."}, status_code=400)

    try:
        await update_schedule_record(
            env,
            schedule_id,
            title=payload.title.strip(),
            description=payload.description.strip(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            assignee_id=payload.assignee_id,
            wbs_task_id=payload.wbs_task_id,
            schedule_type=payload.schedule_type,
        )
        return {"id": schedule_id, "message": "Schedule updated."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to update schedule.", "detail": str(exc)}, status_code=500)


@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, request: Request):
    env = request.scope["env"]
    try:
        await delete_schedule_record(env, schedule_id)
        return {"id": schedule_id, "message": "Schedule deleted."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to delete schedule.", "detail": str(exc)}, status_code=500)


@app.post("/api/document-folders")
async def create_document_folder(request: Request, payload: DocumentFolderPayload):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    if payload.doc_type not in DOCUMENT_TYPES:
        return JSONResponse({"error": "Invalid doc_type."}, status_code=400)

    try:
        folder_id = await create_document_folder_record(
            env,
            doc_type=payload.doc_type,
            folder_name=payload.folder_name,
        )
        if folder_id is None:
            return JSONResponse({"error": "Failed to create folder."}, status_code=500)
        folders = await fetch_document_folders_payload(env, doc_type=payload.doc_type)
        return {"ok": True, "folder_id": folder_id, "folders": folders["folders"]}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to create folder.", "detail": str(exc)}, status_code=500)


@app.post("/api/documents")
async def create_document(request: Request, payload: DocumentPayload):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    if payload.doc_type not in DOCUMENT_TYPES:
        return JSONResponse({"error": "Invalid doc_type."}, status_code=400)

    try:
        folder_id = await _resolve_folder_id(
            env,
            doc_type=payload.doc_type,
            folder_id=payload.folder_id,
            new_folder_name=payload.new_folder_name,
        )
        document_id = await create_document_record(
            env,
            title=payload.title.strip(),
            doc_type=payload.doc_type,
            folder_id=folder_id,
            is_hidden=1 if payload.is_hidden else 0,
            content=payload.content,
            author_id=payload.author_id,
            tags=payload.tags.strip(),
        )
        if document_id is None:
            return JSONResponse({"error": "Failed to create document."}, status_code=500)

        await sync_document_tags(env, document_id, payload.tags)
        await sync_document_task_links(env, document_id, payload.related_task_ids)
        detail = await fetch_document_detail_payload(env, document_id)
        return {"ok": True, "document_id": document_id, "detail": detail}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to create document.", "detail": str(exc)}, status_code=500)


@app.put("/api/documents/{document_id}")
async def update_document(document_id: int, request: Request, payload: DocumentPayload):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    if payload.doc_type not in DOCUMENT_TYPES:
        return JSONResponse({"error": "Invalid doc_type."}, status_code=400)

    existing = await fetch_document_detail_payload(env, document_id)
    if not existing:
        return JSONResponse({"error": "Document not found."}, status_code=404)

    try:
        folder_id = await _resolve_folder_id(
            env,
            doc_type=payload.doc_type,
            folder_id=payload.folder_id,
            new_folder_name=payload.new_folder_name,
        )
        await update_document_record(
            env,
            document_id,
            title=payload.title.strip(),
            doc_type=payload.doc_type,
            folder_id=folder_id,
            is_hidden=1 if payload.is_hidden else 0,
            content=payload.content,
            author_id=payload.author_id,
            tags=payload.tags.strip(),
        )
        await sync_document_tags(env, document_id, payload.tags)
        await sync_document_task_links(env, document_id, payload.related_task_ids)
        detail = await fetch_document_detail_payload(env, document_id)
        return {"ok": True, "document_id": document_id, "detail": detail}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to update document.", "detail": str(exc)}, status_code=500)


@app.put("/api/documents/{document_id}/folder")
async def update_document_folder(document_id: int, request: Request, payload: DocumentFolderPayload):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    if payload.doc_type not in DOCUMENT_TYPES:
        return JSONResponse({"error": "Invalid doc_type."}, status_code=400)

    existing = await fetch_document_detail_payload(env, document_id)
    if not existing:
        return JSONResponse({"error": "Document not found."}, status_code=404)

    try:
        folder_id = await create_document_folder_record(
            env,
            doc_type=payload.doc_type,
            folder_name=payload.folder_name,
        )
        await update_document_folder_record(
            env,
            document_id,
            doc_type=payload.doc_type,
            folder_id=folder_id,
        )
        detail = await fetch_document_detail_payload(env, document_id)
        return {"ok": True, "document_id": document_id, "detail": detail}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to update document folder.", "detail": str(exc)}, status_code=500)


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: int, request: Request):
    env = request.scope["env"]
    if not _has_binding(env, "DB"):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    existing = await fetch_document_detail_payload(env, document_id)
    if not existing:
        return JSONResponse({"error": "Document not found."}, status_code=404)

    try:
        await delete_document_record(env, document_id)
        return {"ok": True, "deleted_id": document_id}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to delete document.", "detail": str(exc)}, status_code=500)


@app.delete("/api/documents/{document_id}/assets/{asset_id}")
async def delete_document_asset(document_id: int, asset_id: int, request: Request):
    env = request.scope["env"]
    if not getattr(env, "DB", None):
        return JSONResponse({"error": "DB binding is not available."}, status_code=503)

    asset = await fetch_document_asset_payload(env, asset_id)
    if not asset or asset.get("document_id") != document_id:
        return JSONResponse({"error": "Document asset not found."}, status_code=404)

    try:
        await _delete_r2_object_if_present(env, asset.get("object_key"))
        await delete_document_asset_record(env, asset_id)
        return {"ok": True, "deleted_id": asset_id, "document_id": document_id}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to delete document asset.", "detail": str(exc)}, status_code=500)


@app.post("/api/wbs")
async def create_wbs(request: Request, payload: WbsPayload):
    env = request.scope["env"]
    if payload.status not in TASK_STATUSES:
        return JSONResponse({"error": "Invalid status."}, status_code=400)
    if payload.priority not in TASK_PRIORITIES:
        return JSONResponse({"error": "Invalid priority."}, status_code=400)
    if payload.platform not in WBS_PLATFORM_OPTIONS:
        return JSONResponse({"error": "Invalid platform."}, status_code=400)
    if not 0 <= payload.progress <= 100:
        return JSONResponse({"error": "progress must be between 0 and 100."}, status_code=400)

    start = _parse_iso_date(payload.start_date)
    due = _parse_iso_date(payload.due_date)
    completed_date = payload.completed_date
    if payload.start_date and not start:
        return JSONResponse({"error": "Invalid start_date format."}, status_code=400)
    if payload.due_date and not due:
        return JSONResponse({"error": "Invalid due_date format."}, status_code=400)
    if start and due and start > due:
        return JSONResponse({"error": "start_date cannot be later than due_date."}, status_code=400)

    progress = payload.progress
    if payload.status == "완료":
        progress = 100
        if not completed_date:
            completed_date = date.today().isoformat()
    elif completed_date and not _parse_iso_date(completed_date):
        return JSONResponse({"error": "Invalid completed_date format."}, status_code=400)

    try:
        task_id = await create_wbs_record(
            env,
            parent_id=payload.parent_id,
            title=payload.title.strip(),
            description=payload.description.strip(),
            assignee_id=payload.assignee_id,
            platform=payload.platform,
            status=payload.status,
            priority=payload.priority,
            start_date=payload.start_date,
            due_date=payload.due_date,
            completed_date=completed_date,
            progress=progress,
            notes=payload.notes.strip(),
        )
        await sync_wbs_task_documents(env, task_id, payload.document_ids)
        return {"id": task_id, "message": "WBS task created."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to create WBS task.", "detail": str(exc)}, status_code=500)


@app.put("/api/wbs/{task_id}")
async def update_wbs(task_id: int, request: Request, payload: WbsPayload):
    env = request.scope["env"]
    if payload.status not in TASK_STATUSES:
        return JSONResponse({"error": "Invalid status."}, status_code=400)
    if payload.priority not in TASK_PRIORITIES:
        return JSONResponse({"error": "Invalid priority."}, status_code=400)
    if payload.platform not in WBS_PLATFORM_OPTIONS:
        return JSONResponse({"error": "Invalid platform."}, status_code=400)
    if not 0 <= payload.progress <= 100:
        return JSONResponse({"error": "progress must be between 0 and 100."}, status_code=400)
    if payload.parent_id == task_id:
        return JSONResponse({"error": "A task cannot be its own parent."}, status_code=400)

    start = _parse_iso_date(payload.start_date)
    due = _parse_iso_date(payload.due_date)
    completed_date = payload.completed_date
    if payload.start_date and not start:
        return JSONResponse({"error": "Invalid start_date format."}, status_code=400)
    if payload.due_date and not due:
        return JSONResponse({"error": "Invalid due_date format."}, status_code=400)
    if start and due and start > due:
        return JSONResponse({"error": "start_date cannot be later than due_date."}, status_code=400)

    progress = payload.progress
    if payload.status == "완료":
        progress = 100
        if not completed_date:
            completed_date = date.today().isoformat()
    elif completed_date and not _parse_iso_date(completed_date):
        return JSONResponse({"error": "Invalid completed_date format."}, status_code=400)

    try:
        await update_wbs_record(
            env,
            task_id,
            parent_id=payload.parent_id,
            title=payload.title.strip(),
            description=payload.description.strip(),
            assignee_id=payload.assignee_id,
            platform=payload.platform,
            status=payload.status,
            priority=payload.priority,
            start_date=payload.start_date,
            due_date=payload.due_date,
            completed_date=completed_date,
            progress=progress,
            notes=payload.notes.strip(),
        )
        await sync_wbs_task_documents(env, task_id, payload.document_ids)
        return {"id": task_id, "message": "WBS task updated."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to update WBS task.", "detail": str(exc)}, status_code=500)


@app.delete("/api/wbs/{task_id}")
async def delete_wbs(task_id: int, request: Request):
    env = request.scope["env"]
    try:
        await delete_wbs_record(env, task_id)
        return {"id": task_id, "message": "WBS task deleted."}
    except Exception as exc:  # pragma: no cover - runtime-specific fallback
        return JSONResponse({"error": "Failed to delete WBS task.", "detail": str(exc)}, status_code=500)
