from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evisuff.experiment_cli import load_env_file


class ExperimentEnvTests(unittest.TestCase):
    def test_env_file_loads_secrets_for_execution_without_overwriting_process_env(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / ".env"
            path.write_text(
                "API_KEY=file-secret\nMODEL='frozen-model-id'\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"API_KEY": "process-secret"}, clear=True):
                load_env_file(path)
                self.assertEqual(os.environ["API_KEY"], "process-secret")
                self.assertEqual(os.environ["MODEL"], "frozen-model-id")

    def test_invalid_env_line_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / ".env"
            path.write_text("NOT_AN_ASSIGNMENT\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected KEY=VALUE"):
                load_env_file(path)


if __name__ == "__main__":
    unittest.main()
