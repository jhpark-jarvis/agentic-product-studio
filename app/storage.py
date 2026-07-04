from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import boto3
from botocore.client import Config
from flask import current_app


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def is_r2_enabled() -> bool:
    return (
        current_app.config.get("STORAGE_BACKEND") == "r2"
        and bool(current_app.config.get("R2_ACCOUNT_ID"))
        and bool(current_app.config.get("R2_ACCESS_KEY_ID"))
        and bool(current_app.config.get("R2_SECRET_ACCESS_KEY"))
    )


def is_allowed_image(filename: str | None) -> bool:
    if not filename:
        return False
    return Path(filename).suffix.lower() in ALLOWED_IMAGE_EXTENSIONS


def build_object_key(folder: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{folder}/{uuid4().hex}{suffix}"


def public_asset_url(object_key: str) -> str:
    base_url = (current_app.config.get("R2_PUBLIC_BASE_URL") or "").rstrip("/")
    if base_url:
        return f"{base_url}/{object_key}"

    if is_r2_enabled():
        account_id = current_app.config["R2_ACCOUNT_ID"]
        bucket = current_app.config["R2_BUCKET_NAME"]
        return f"https://pub-{account_id}.r2.dev/{bucket}/{object_key}"

    return f"/uploads/{object_key}"


def _r2_client():
    account_id = current_app.config["R2_ACCOUNT_ID"]
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=current_app.config["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_image(file_storage, folder: str = "documents") -> dict[str, str]:
    object_key = build_object_key(folder, file_storage.filename or "image")
    content_type = file_storage.mimetype or "application/octet-stream"

    if is_r2_enabled():
        client = _r2_client()
        client.upload_fileobj(
            file_storage.stream,
            current_app.config["R2_BUCKET_NAME"],
            object_key,
            ExtraArgs={"ContentType": content_type},
        )
        return {"object_key": object_key, "url": public_asset_url(object_key)}

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / folder
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / Path(object_key).name
    file_storage.save(target)
    return {
        "object_key": f"{folder}/{target.name}",
        "url": public_asset_url(f"{folder}/{target.name}"),
    }
