from __future__ import annotations

from io import BytesIO
from pathlib import Path
import hashlib
from uuid import uuid4

import boto3
from botocore.client import Config
from flask import current_app, send_file


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def missing_r2_config_fields() -> list[str]:
    required = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    return [key for key in required if not current_app.config.get(key)]


def is_r2_enabled() -> bool:
    return (
        current_app.config.get("STORAGE_BACKEND") == "r2"
        and not missing_r2_config_fields()
    )


def is_allowed_image(filename: str | None) -> bool:
    if not filename:
        return False
    return Path(filename).suffix.lower() in ALLOWED_IMAGE_EXTENSIONS


def build_object_key(folder: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{folder}/{uuid4().hex}{suffix}"


def _stream_size_and_checksum(file_storage) -> tuple[int, str]:
    file_storage.stream.seek(0)
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = file_storage.stream.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        digest.update(chunk)
    file_storage.stream.seek(0)
    return total, digest.hexdigest()


def public_asset_url(object_key: str) -> str:
    base_url = (current_app.config.get("R2_PUBLIC_BASE_URL") or "").rstrip("/")
    if base_url:
        return f"{base_url}/{object_key}"

    if is_r2_enabled():
        account_id = current_app.config["R2_ACCOUNT_ID"]
        return f"https://pub-{account_id}.r2.dev/{object_key}"

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
    return upload_file(file_storage, folder=folder)


def upload_file(file_storage, folder: str = "assets") -> dict[str, str]:
    object_key = build_object_key(folder, file_storage.filename or "file")
    content_type = file_storage.mimetype or "application/octet-stream"
    size, checksum = _stream_size_and_checksum(file_storage)

    if current_app.config.get("STORAGE_BACKEND") == "r2" and not is_r2_enabled():
        missing = ", ".join(missing_r2_config_fields())
        raise RuntimeError(f"R2 storage is selected but missing configuration: {missing}")

    if is_r2_enabled():
        client = _r2_client()
        client.upload_fileobj(
            file_storage.stream,
            current_app.config["R2_BUCKET_NAME"],
            object_key,
            ExtraArgs={"ContentType": content_type},
        )
        return {
            "object_key": object_key,
            "url": public_asset_url(object_key),
            "content_type": content_type,
            "size": str(size),
            "checksum": checksum,
        }

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / folder
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / Path(object_key).name
    file_storage.save(target)
    return {
        "object_key": f"{folder}/{target.name}",
        "url": public_asset_url(f"{folder}/{target.name}"),
        "content_type": content_type,
        "size": str(size),
        "checksum": checksum,
    }


def delete_object(object_key: str) -> None:
    if not object_key:
        return

    if is_r2_enabled():
        client = _r2_client()
        client.delete_object(Bucket=current_app.config["R2_BUCKET_NAME"], Key=object_key)
        return

    target = Path(current_app.config["UPLOAD_FOLDER"]) / object_key
    if target.exists():
        target.unlink()


def read_object_bytes(object_key: str) -> tuple[bytes, str | None]:
    if not object_key:
        raise FileNotFoundError("Missing object key")

    if is_r2_enabled():
        client = _r2_client()
        response = client.get_object(
            Bucket=current_app.config["R2_BUCKET_NAME"],
            Key=object_key,
        )
        return response["Body"].read(), response.get("ContentType")

    target = Path(current_app.config["UPLOAD_FOLDER"]) / object_key
    if not target.exists():
        raise FileNotFoundError(object_key)
    return target.read_bytes(), None


def download_object(*, object_key: str, download_name: str, content_type: str | None = None):
    if not object_key:
        raise FileNotFoundError("Missing object key")

    body, detected_content_type = read_object_bytes(object_key)
    resolved_content_type = content_type or detected_content_type or "application/octet-stream"
    return send_file(
        BytesIO(body),
        mimetype=resolved_content_type,
        as_attachment=True,
        download_name=download_name,
    )
