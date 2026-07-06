import os
from pathlib import Path

import click
from flask import Flask
from dotenv import load_dotenv

from .dashboard import bp as dashboard_bp
from .db import close_db, init_app as init_db_app, init_db
from .documents import bp as documents_bp
from .members import bp as members_bp
from .repositories.provider import get_repository_provider
from .schedules import bp as schedules_bp
from .storage import is_r2_enabled, missing_r2_config_fields
from .utils import (
    DEFAULT_TIMEZONE,
    css_badge_class,
    format_datetime_local,
    markdown_to_html,
    today_local,
)
from .wbs import bp as wbs_bp


def create_app(test_config=None):
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")
    app = Flask(__name__, instance_relative_config=True)

    base_dir = Path(app.root_path).parent
    upload_dir = base_dir / "uploads"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.environ.get("DATABASE", str(Path(app.instance_path) / "app.db")),
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", str(upload_dir)),
        MAX_CONTENT_LENGTH=int(os.environ.get("MAX_CONTENT_LENGTH", 20 * 1024 * 1024)),
        DISPLAY_TIMEZONE=os.environ.get("DISPLAY_TIMEZONE", DEFAULT_TIMEZONE),
        STORAGE_BACKEND=os.environ.get("STORAGE_BACKEND", "local"),
        REPOSITORY_BACKEND=os.environ.get("REPOSITORY_BACKEND", "sqlite"),
        CLOUDFLARE_ACCOUNT_ID=os.environ.get(
            "CLOUDFLARE_ACCOUNT_ID", os.environ.get("R2_ACCOUNT_ID", "")
        ),
        D1_DATABASE_ID=os.environ.get(
            "D1_DATABASE_ID", "<D1_DATABASE_ID>"
        ),
        CLOUDFLARE_API_TOKEN=os.environ.get("CLOUDFLARE_API_TOKEN", ""),
        R2_BUCKET_NAME=os.environ.get("R2_BUCKET_NAME", "<R2_BUCKET_NAME>"),
        R2_ACCOUNT_ID=os.environ.get("R2_ACCOUNT_ID", ""),
        R2_ACCESS_KEY_ID=os.environ.get("R2_ACCESS_KEY_ID", ""),
        R2_SECRET_ACCESS_KEY=os.environ.get("R2_SECRET_ACCESS_KEY", ""),
        R2_PUBLIC_BASE_URL=os.environ.get("R2_PUBLIC_BASE_URL", ""),
        FLASK_ENV=os.environ.get("FLASK_ENV", "development"),
        FLASK_DEBUG=os.environ.get("FLASK_DEBUG", "0") == "1",
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(wbs_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(members_bp)
    app.teardown_appcontext(close_db)
    init_db_app(app)
    app.jinja_env.filters["markdown"] = markdown_to_html
    app.jinja_env.filters["datetime_local"] = format_datetime_local
    app.jinja_env.filters["badge_class"] = css_badge_class

    # Initialize the small local SQLite schema on first run.
    with app.app_context():
        init_db()

    @app.cli.command("cloudflare-check")
    def cloudflare_check():
        """Validate the Flask frontend + Cloudflare backend connection path."""
        provider = get_repository_provider()
        summary = provider.dashboard.fetch_dashboard_summary(today_local().isoformat())
        active_members = provider.common.fetch_active_members()

        click.echo("Cloudflare backend check")
        click.echo(f"- repository backend: {app.config['REPOSITORY_BACKEND']}")
        click.echo(f"- storage backend: {app.config['STORAGE_BACKEND']}")
        click.echo(f"- dashboard summary loaded: {'yes' if summary is not None else 'no'}")
        click.echo(f"- active members fetched: {len(active_members)}")
        click.echo(f"- R2 mode enabled: {'yes' if is_r2_enabled() else 'no'}")
        click.echo(f"- R2 public base url configured: {'yes' if app.config.get('R2_PUBLIC_BASE_URL') else 'no'}")
        missing_fields = missing_r2_config_fields()
        click.echo(f"- missing R2 config fields: {', '.join(missing_fields) if missing_fields else 'none'}")

    return app
