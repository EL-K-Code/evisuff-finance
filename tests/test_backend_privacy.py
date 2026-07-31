from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from evisuff.model_backends import CommandBackend, ModelRequest


class BackendPrivacyTests(unittest.TestCase):
    def test_command_backend_never_receives_private_gold_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "echo_metadata.py"
            script.write_text(
                textwrap.dedent(
                    """
                    import json
                    import sys

                    payload = json.load(sys.stdin)
                    parsed = {"metadata": payload["metadata"]}
                    print(json.dumps({"content": json.dumps(parsed), "parsed": parsed}))
                    """
                ),
                encoding="utf-8",
            )
            backend = CommandBackend([sys.executable, str(script)])
            request = ModelRequest(
                request_id="privacy-test",
                workflow_id="workflow",
                condition="isolated",
                department="diligence",
                system_prompt="system",
                user_prompt="user",
                metadata={
                    "spec": {"versions": {"v2": {"facts": {"gold": 1}}}},
                    "repetition": 1,
                },
            )
            response = backend.generate(request)
            self.assertIsNotNone(response.parsed)
            metadata = response.parsed["metadata"]
            self.assertNotIn("spec", metadata)
            self.assertEqual(metadata["repetition"], 1)


if __name__ == "__main__":
    unittest.main()
