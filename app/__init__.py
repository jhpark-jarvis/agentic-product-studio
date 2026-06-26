from pathlib import Path

from flask import Flask

from .dashboard import bp as dashboard_bp
from .db import close_db, init_app as init_db_app, init_db
from .documents import bp as documents_bp
from .members import bp as members_bp
from .schedules import bp as schedules_bp
from .utils import DEFAULT_TIMEZONE, css_badge_class, format_datetime_local, markdown_to_html
from .wbs import bp as wbs_bp


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    base_dir = Path(app.root_path).parent
    upload_dir = base_dir / "uploads"

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=str(Path(app.instance_path) / "app.db"),
        UPLOAD_FOLDER=str(upload_dir),
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
        DISPLAY_TIMEZONE=DEFAULT_TIMEZONE,
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    upload_dir.mkdir(parents=True, exist_ok=True)

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

    return app
