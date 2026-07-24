from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv

from .utils import DEFAULT_TIMEZONE


@dataclass(slots=True)
class AppSettings:
    secret_key: str
    database: str
    upload_folder: str
    max_content_length: int
    display_timezone: str
    storage_backend: str
    repository_backend: str
    cloudflare_account_id: str
    d1_database_id: str
    cloudflare_api_token: str
    r2_bucket_name: str
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_public_base_url: str
    flask_env: str
    flask_debug: bool
    instance_path: str
    project_root: str

    def to_config_mapping(self) -> dict[str, object]:
        values = asdict(self)
        return {
            "SECRET_KEY": values["secret_key"],
            "DATABASE": values["database"],
            "UPLOAD_FOLDER": values["upload_folder"],
            "MAX_CONTENT_LENGTH": values["max_content_length"],
            "DISPLAY_TIMEZONE": values["display_timezone"],
            "STORAGE_BACKEND": values["storage_backend"],
            "REPOSITORY_BACKEND": values["repository_backend"],
            "CLOUDFLARE_ACCOUNT_ID": values["cloudflare_account_id"],
            "D1_DATABASE_ID": values["d1_database_id"],
            "CLOUDFLARE_API_TOKEN": values["cloudflare_api_token"],
            "R2_BUCKET_NAME": values["r2_bucket_name"],
            "R2_ACCOUNT_ID": values["r2_account_id"],
            "R2_ACCESS_KEY_ID": values["r2_access_key_id"],
            "R2_SECRET_ACCESS_KEY": values["r2_secret_access_key"],
            "R2_PUBLIC_BASE_URL": values["r2_public_base_url"],
            "FLASK_ENV": values["flask_env"],
            "FLASK_DEBUG": values["flask_debug"],
            "INSTANCE_PATH": values["instance_path"],
            "PROJECT_ROOT": values["project_root"],
        }


def load_settings(*, env_file: str | Path | None = None) -> AppSettings:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(env_file or (project_root / ".env"))

    instance_path = project_root / "instance"
    upload_dir = project_root / "uploads"
    instance_path.mkdir(parents=True, exist_ok=True)
    upload_dir.mkdir(parents=True, exist_ok=True)

    return AppSettings(
        secret_key=os.environ.get("SECRET_KEY", "dev"),
        database=os.environ.get("DATABASE", str(instance_path / "app.db")),
        upload_folder=os.environ.get("UPLOAD_FOLDER", str(upload_dir)),
        max_content_length=int(os.environ.get("MAX_CONTENT_LENGTH", 20 * 1024 * 1024)),
        display_timezone=os.environ.get("DISPLAY_TIMEZONE", DEFAULT_TIMEZONE),
        storage_backend=os.environ.get("STORAGE_BACKEND", "local"),
        repository_backend=os.environ.get("REPOSITORY_BACKEND", "sqlite"),
        cloudflare_account_id=os.environ.get(
            "CLOUDFLARE_ACCOUNT_ID",
            os.environ.get("R2_ACCOUNT_ID", ""),
        ),
        d1_database_id=os.environ.get("D1_DATABASE_ID", ""),
        cloudflare_api_token=os.environ.get("CLOUDFLARE_API_TOKEN", ""),
        r2_bucket_name=os.environ.get("R2_BUCKET_NAME", ""),
        r2_account_id=os.environ.get("R2_ACCOUNT_ID", ""),
        r2_access_key_id=os.environ.get("R2_ACCESS_KEY_ID", ""),
        r2_secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY", ""),
        r2_public_base_url=os.environ.get("R2_PUBLIC_BASE_URL", ""),
        flask_env=os.environ.get("FLASK_ENV", "development"),
        flask_debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        instance_path=str(instance_path),
        project_root=str(project_root),
    )
