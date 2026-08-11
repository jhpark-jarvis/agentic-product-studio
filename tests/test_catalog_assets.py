from __future__ import annotations

import asyncio
from io import BytesIO
import json
import sqlite3
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

from app.db import initialize_database
from app.catalog_assets import download_catalog_thumbnail_png, search_catalog_assets
from fastapi_app.routers.catalog_assets import _import_asset, _sync_avatar_catalog


class FakeResponse(BytesIO):
    def __init__(self, body: bytes, content_type: str):
        super().__init__(body)
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class CatalogAssetsTests(unittest.TestCase):
    def test_import_keeps_sqlite_repository_work_on_request_thread(self):
        request_thread_id = threading.get_ident()
        repository_thread_ids = []
        worker_thread_ids = []

        class AssetRepository:
            def fetch_asset_by_source(self, *_args):
                repository_thread_ids.append(threading.get_ident())
                return None

            def create_asset(self, _data):
                repository_thread_ids.append(threading.get_ident())
                return 7

            def fetch_asset(self, _asset_id):
                repository_thread_ids.append(threading.get_ident())
                return {"id": 7, "title": "테스트 헤어"}

        def prepare_asset(*, resource_id, settings):
            worker_thread_ids.append(threading.get_ident())
            return (
                {
                    "resource_id": resource_id,
                    "name": "테스트 헤어",
                    "category": "hair",
                    "thumbnail_url": "https://example.test/source.webp",
                },
                {"filename": f"{resource_id}.png", "content_type": "image/png"},
                {
                    "filename": f"{resource_id}.png",
                    "object_key": f"assets/catalog/{resource_id}.png",
                    "url": f"/uploads/assets/catalog/{resource_id}.png",
                    "content_type": "image/png",
                    "size": 10,
                    "checksum": "checksum",
                },
            )

        provider = SimpleNamespace(assets=AssetRepository())
        settings = SimpleNamespace(max_content_length=1024, to_config_mapping=lambda: {})
        with patch(
            "fastapi_app.routers.catalog_assets._download_and_store_asset",
            side_effect=prepare_asset,
        ):
            asset, created, source_item = asyncio.run(
                _import_asset(resource_id="d" * 32, provider=provider, settings=settings)
            )

        self.assertTrue(created)
        self.assertEqual(7, asset["id"])
        self.assertEqual("d" * 32, source_item["resource_id"])
        self.assertTrue(repository_thread_ids)
        self.assertTrue(all(thread_id == request_thread_id for thread_id in repository_thread_ids))
        self.assertTrue(worker_thread_ids)
        self.assertNotEqual(request_thread_id, worker_thread_ids[0])

    def test_avatar_catalog_sync_upserts_every_group_member(self):
        selected_resource_id = "a" * 32
        existing_master_resource_id = "b" * 32
        records_written = []
        replace_values = []

        class AvatarRepository:
            def fetch_catalog_group(self, **_kwargs):
                return {
                    "master_resource_id": existing_master_resource_id,
                    "name": "기존 카탈로그 이름",
                    "source_index": 3,
                }

            def replace_catalog(self, records, *, replace):
                replace_values.append(replace)
                records_written.extend(records)
                return {"asset_count": 1, "variant_count": len(records)}

        provider = SimpleNamespace(avatar_assets=AvatarRepository())
        item = {
            "resource_id": selected_resource_id,
            "name": "테스트 헤어",
            "category": "hair",
            "group_id": "hair:test",
            "group_canonical": False,
            "variants": [
                {
                    "resource_id": selected_resource_id,
                    "name": "검은색 테스트 헤어",
                    "dname": "hair-1",
                    "color_hex": "#111111",
                    "thumbnail_url": "https://example.test/a.webp",
                },
                {
                    "resource_id": existing_master_resource_id,
                    "name": "갈색 테스트 헤어",
                    "dname": "hair-2",
                    "color_hex": "#222222",
                    "thumbnail_url": "https://example.test/b.webp",
                },
            ],
        }

        result = _sync_avatar_catalog(item=item, gender="female", provider=provider)

        self.assertEqual(2, result["variant_count"])
        self.assertEqual([False], replace_values)
        self.assertEqual({selected_resource_id, existing_master_resource_id}, {
            record["variant_resource_id"] for record in records_written
        })
        self.assertTrue(all(
            record["master_resource_id"] == existing_master_resource_id for record in records_written
        ))
        self.assertTrue(all(
            record["name"] == "기존 카탈로그 이름" for record in records_written
        ))

    def test_initialize_database_migrates_existing_asset_tables_before_creating_indexes(self):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.executescript(
            """
            CREATE TABLE assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            CREATE TABLE document_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        initialize_database(db)

        asset_columns = {row[1] for row in db.execute("PRAGMA table_info(assets)")}
        document_asset_columns = {
            row[1] for row in db.execute("PRAGMA table_info(document_assets)")
        }
        index_names = {row[1] for row in db.execute("PRAGMA index_list(assets)")}
        self.assertIn("source_provider", asset_columns)
        self.assertIn("linked_asset_id", document_asset_columns)
        self.assertIn("idx_assets_external_source", index_names)

    def test_search_groups_duplicate_results_and_builds_variants(self):
        first_resource_id = "a" * 32
        second_resource_id = "b" * 32
        payload = {
            "results": [
                {
                    "id": first_resource_id,
                    "type": "avataritem",
                    "category": "hair",
                    "names": {"ko": ["검은색 테스트 헤어"]},
                    "dname": "hair-1",
                    "payload": {
                        "group_id": "hair:test",
                        "group_members": [
                            {
                                "resource_id": first_resource_id,
                                "color": "#111111",
                                "names": {"ko": ["검은색 테스트 헤어"]},
                                "dname": "hair-1",
                            },
                            {
                                "resource_id": second_resource_id,
                                "color": "#222222",
                                "names": {"ko": ["갈색 테스트 헤어"]},
                                "dname": "hair-2",
                            },
                        ],
                    },
                },
                {
                    "id": second_resource_id,
                    "type": "avataritem",
                    "category": "hair",
                    "names": {"ko": ["갈색 테스트 헤어"]},
                    "dname": "hair-2",
                    "payload": {
                        "group_id": "hair:test",
                        "group_members": [],
                    },
                },
            ],
            "nextOffset": 2,
            "exactMatch": False,
        }
        response = FakeResponse(json.dumps(payload).encode("utf-8"), "application/json")
        with patch("app.catalog_assets.urlopen", return_value=response):
            result = search_catalog_assets("테스트 헤어", limit=2)

        self.assertEqual(1, len(result["items"]))
        self.assertEqual(2, len(result["items"][0]["variants"]))
        self.assertTrue(result["pagination"]["has_more"])

    def test_download_converts_webp_to_rgba_png(self):
        source = BytesIO()
        Image.new("RGBA", (2, 2), (10, 20, 30, 40)).save(source, format="WEBP")
        response = FakeResponse(source.getvalue(), "image/webp")

        with patch("app.catalog_assets.urlopen", return_value=response):
            result = download_catalog_thumbnail_png("c" * 32, max_download_size=1024 * 1024)

        self.assertEqual("image/png", result["content_type"])
        self.assertEqual(b"\x89PNG\r\n\x1a\n", result["stream"].read(8))


if __name__ == "__main__":
    unittest.main()
