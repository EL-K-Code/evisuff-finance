from __future__ import annotations

import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "list_provider_models.py"
SPEC = importlib.util.spec_from_file_location("list_provider_models", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
list_provider_models = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(list_provider_models)


class _ModelsHandler(BaseHTTPRequestHandler):
    request_path = ""
    request_headers: dict[str, str] = {}
    response_payload: dict = {}

    def do_GET(self) -> None:  # noqa: N802
        type(self).request_path = self.path
        type(self).request_headers = {
            key.lower(): value for key, value in self.headers.items()
        }
        body = json.dumps(type(self).response_payload).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class ProviderModelDiscoveryTests(unittest.TestCase):
    def _serve(self, payload: dict) -> tuple[ThreadingHTTPServer, threading.Thread]:
        _ModelsHandler.response_payload = payload
        server = ThreadingHTTPServer(("127.0.0.1", 0), _ModelsHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_openai_compatible_model_list(self) -> None:
        server, thread = self._serve(
            {"data": [{"id": "model-b"}, {"id": "model-a"}, {"id": "model-a"}]}
        )
        try:
            models = list_provider_models.fetch_model_ids(
                base_url=f"http://127.0.0.1:{server.server_port}/v1",
                api_key="bearer-key",
                auth="bearer",
            )
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
        self.assertEqual(models, ["model-a", "model-b"])
        self.assertEqual(_ModelsHandler.request_path, "/v1/models")
        self.assertEqual(
            _ModelsHandler.request_headers.get("authorization"), "Bearer bearer-key"
        )

    def test_anthropic_model_list_headers_and_shape(self) -> None:
        server, thread = self._serve(
            {"models": [{"id": "claude-b"}, {"name": "claude-a"}]}
        )
        try:
            models = list_provider_models.fetch_model_ids(
                base_url=f"http://127.0.0.1:{server.server_port}/v1",
                api_key="anthropic-key",
                auth="anthropic",
            )
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
        self.assertEqual(models, ["claude-a", "claude-b"])
        self.assertEqual(_ModelsHandler.request_headers.get("x-api-key"), "anthropic-key")
        self.assertEqual(
            _ModelsHandler.request_headers.get("anthropic-version"), "2023-06-01"
        )


if __name__ == "__main__":
    unittest.main()
