"""Legacy Flask compatibility entrypoint.

FastAPI is the primary application runtime. Keep this entrypoint while the
ASGI deployment is being verified and the remaining Flask compatibility
commands are being retired.
"""

from app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config.get("FLASK_DEBUG", False))
