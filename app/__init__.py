from pathlib import Path

import click
from flask import Flask

from .api import bp as api_bp
from .db import close_db, init_app as init_db_app, init_db
from .documents import bp as documents_bp
from .frontend import bp as frontend_bp
from .page_view_logging import setup_page_view_logger
from .repositories.provider import get_repository_provider
from .settings import AppSettings, load_settings
from .storage import is_r2_enabled, missing_r2_config_fields
from .utils import (
    css_badge_class,
    format_datetime_local,
    markdown_to_html,
    today_local,
)


def _apply_flask_settings(app: Flask, settings: AppSettings) -> None:
    app.config.from_mapping(settings.to_config_mapping())
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DATABASE"] = settings.database
    app.config["UPLOAD_FOLDER"] = settings.upload_folder
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length
    app.config["DISPLAY_TIMEZONE"] = settings.display_timezone
    app.config["STORAGE_BACKEND"] = settings.storage_backend
    app.config["REPOSITORY_BACKEND"] = settings.repository_backend
    app.config["FLASK_ENV"] = settings.flask_env
    app.config["FLASK_DEBUG"] = settings.flask_debug


def create_app(test_config=None, *, settings: AppSettings | None = None):
    app = Flask(__name__, instance_relative_config=True)
    resolved_settings = settings or load_settings()
    _apply_flask_settings(app, resolved_settings)

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    app.register_blueprint(documents_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(frontend_bp)
    app.teardown_appcontext(close_db)
    init_db_app(app)
    setup_page_view_logger(app)
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
