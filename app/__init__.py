from pathlib import Path

from flask import Flask

from .db import close_db, init_app as init_db_app, init_db
from .routes import bp as main_bp


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    base_dir = Path(app.root_path).parent
    upload_dir = base_dir / "uploads"

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=str(Path(app.instance_path) / "app.db"),
        UPLOAD_FOLDER=str(upload_dir),
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    upload_dir.mkdir(parents=True, exist_ok=True)

    app.register_blueprint(main_bp)
    app.teardown_appcontext(close_db)
    init_db_app(app)

    # Initialize the small local SQLite schema on first run.
    with app.app_context():
        init_db()

    return app
