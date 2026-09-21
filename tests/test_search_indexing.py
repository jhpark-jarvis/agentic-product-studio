from __future__ import annotations

import asyncio
import unittest

from fastapi import FastAPI

from fastapi_app.main import (
    SEARCH_EXCLUSION_DIRECTIVE,
    install_search_exclusion_headers,
)


async def request_headers(app: FastAPI, path: str) -> tuple[int, dict[str, str]]:
    request_sent = False
    messages = []

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )

    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    headers = {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in response_start["headers"]
    }
    return response_start["status"], headers


class SearchIndexingTests(unittest.TestCase):
    def test_search_exclusion_header_is_added_to_every_response(self):
        app = FastAPI()
        install_search_exclusion_headers(app)

        @app.get("/probe")
        async def probe():
            return {"ok": True}

        status, headers = asyncio.run(request_headers(app, "/probe"))
        missing_status, missing_headers = asyncio.run(request_headers(app, "/missing"))

        self.assertEqual(200, status)
        self.assertEqual(
            SEARCH_EXCLUSION_DIRECTIVE,
            headers["x-robots-tag"],
        )
        self.assertEqual(404, missing_status)
        self.assertEqual(
            SEARCH_EXCLUSION_DIRECTIVE,
            missing_headers["x-robots-tag"],
        )


if __name__ == "__main__":
    unittest.main()
