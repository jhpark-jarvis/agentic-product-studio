from workers import WorkerEntrypoint

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import asgi


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)


app = FastAPI(
    title="Agentic Product Studio Cloudflare Worker",
    version="0.1.0",
)


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
        "has_db_binding": bool(getattr(env, "DB", None)),
        "has_image_bucket_binding": bool(getattr(env, "DOCUMENT_IMAGES", None)),
    }


@app.get("/api/runtime-summary")
async def runtime_summary(request: Request):
    env = request.scope["env"]

    summary = {
        "worker_runtime": "python-workers-beta",
        "bindings": {
            "db": bool(getattr(env, "DB", None)),
            "document_images": bool(getattr(env, "DOCUMENT_IMAGES", None)),
        },
    }

    if not getattr(env, "DB", None):
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
    if not getattr(env, "DB", None):
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
