from pathlib import Path

from flask import Blueprint, current_app, render_template

from .db import get_db


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    db = get_db()
    docs_count = db.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
    assets_count = db.execute("SELECT COUNT(*) AS count FROM assets").fetchone()["count"]
    recent_documents = db.execute(
        """
        SELECT id, title, doc_type, created_at
        FROM documents
        ORDER BY created_at DESC, id DESC
        LIMIT 5
        """
    ).fetchall()
    recent_assets = db.execute(
        """
        SELECT id, title, file_name, created_at
        FROM assets
        ORDER BY created_at DESC, id DESC
        LIMIT 5
        """
    ).fetchall()

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_count = sum(1 for path in upload_dir.iterdir() if path.is_file()) if upload_dir.exists() else 0

    return render_template(
        "index.html",
        docs_count=docs_count,
        assets_count=assets_count,
        upload_count=upload_count,
        recent_documents=recent_documents,
        recent_assets=recent_assets,
    )
