from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from evisuff.model_backends import AnthropicMessagesBackend, ModelRequest


class _AnthropicHandler(BaseHTTPRequestHandler):
    request_body: dict = {}
    request_headers: dict = {}

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        type(self).request_body = json.loads(self.rfile.read(length))
        type(self).request_headers = {
            key.lower(): value for key, value in self.headers.items()
        }
        payload = {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": '{"ok": true}'}],
            "usage": {"input_tokens": 12, "output_tokens": 4},
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class AnthropicBackendTests(unittest.TestCase):
    def test_native_messages_request_and_usage(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _AnthropicHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            backend = AnthropicMessagesBackend(
                model="claude-test-snapshot",
                api_key="test-key",
                base_url=f"http://127.0.0.1:{server.server_port}/v1",
                max_retries=0,
            )
            response = backend.generate(
                ModelRequest(
                    request_id="anthropic-test",
                    workflow_id="workflow",
                    condition="generalist",
                    department=None,
                    system_prompt="Return JSON only",
                    user_prompt="Complete the workflow",
                    metadata={},
                )
            )
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

        self.assertEqual(response.parsed, {"ok": True})
        self.assertEqual(response.input_tokens, 12)
        self.assertEqual(response.output_tokens, 4)
        self.assertEqual(_AnthropicHandler.request_body["model"], "claude-test-snapshot")
        self.assertEqual(_AnthropicHandler.request_body["system"], "Return JSON only")
        self.assertEqual(_AnthropicHandler.request_headers.get("x-api-key"), "test-key")
        self.assertEqual(
            _AnthropicHandler.request_headers.get("anthropic-version"), "2023-06-01"
        )


if __name__ == "__main__":
    unittest.main()
