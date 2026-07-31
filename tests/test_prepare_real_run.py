from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "prepare_real_run.py"
SPEC = importlib.util.spec_from_file_location("prepare_real_run", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare_real_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_real_run)


class PrepareRealRunTests(unittest.TestCase):
    def test_generated_config_references_env_names_without_serializing_secrets(self) -> None:
        environment = {
            "ENABLE_QWEN": "true",
            "QWEN_API_KEY": "super-secret-key",
            "QWEN_API_BASE": "https://example.test/v1",
            "QWEN_MODEL": "qwen-test-snapshot",
            "QWEN_INPUT_PRICE_USD_PER_MTOK": "1.25",
            "QWEN_OUTPUT_PRICE_USD_PER_MTOK": "3.50",
        }
        with patch.dict(os.environ, environment, clear=True):
            config, warnings = prepare_real_run.build_config(3)
        serialized = json.dumps(config)
        self.assertNotIn("super-secret-key", serialized)
        self.assertEqual(warnings, [])
        self.assertEqual(config["repetitions"], 3)
        self.assertEqual(len(config["cases"]), 3)
        system = config["systems"][0]
        self.assertEqual(system["system_id"], "qwen::qwen-test-snapshot")
        self.assertEqual(system["backend"]["api_key_env"], "QWEN_API_KEY")
        self.assertEqual(system["backend"]["model_env"], "QWEN_MODEL")

    def test_no_enabled_provider_is_rejected(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "No provider enabled"):
                prepare_real_run.build_config(1)

    def test_env_loader_preserves_existing_process_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / ".env"
            path.write_text(
                "QWEN_API_KEY=file-value\nENABLE_QWEN=true\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"QWEN_API_KEY": "process-value"}, clear=True):
                prepare_real_run.load_env(path)
                self.assertEqual(os.environ["QWEN_API_KEY"], "process-value")
                self.assertEqual(os.environ["ENABLE_QWEN"], "true")

    def test_invalid_repetition_count_is_rejected(self) -> None:
        environment = {
            "ENABLE_QWEN": "true",
            "QWEN_API_KEY": "key",
            "QWEN_API_BASE": "https://example.test/v1",
            "QWEN_MODEL": "model",
        }
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(ValueError, "at least 1"):
                prepare_real_run.build_config(0)


if __name__ == "__main__":
    unittest.main()
