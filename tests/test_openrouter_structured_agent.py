from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from tools import openrouter_structured_agent as agent


class OpenRouterStructuredAgentTests(unittest.TestCase):
    def test_self_test_passes(self) -> None:
        agent.self_test()

    def test_extract_content_accepts_openai_shape(self) -> None:
        payload = {
            "choices": [
                {"message": {"content": '{"risk_flags": []}'}}
            ]
        }
        self.assertEqual(agent._extract_content(payload), '{"risk_flags": []}')

    def test_parse_structured_content_accepts_fenced_json(self) -> None:
        payload = {
            "department": "risk",
            "source_version": "v2",
            "scenario_id": "base_case",
            "risk_flags": ["ftc_data_licensing_inquiry"],
        }
        content = "```json\n" + json.dumps(payload) + "\n```"
        self.assertEqual(agent._parse_structured_content(content, "risk"), payload)

    def test_parse_structured_content_accepts_harmony_final_channel(self) -> None:
        payload = {
            "department": "risk",
            "source_version": "v2",
            "scenario_id": "base_case",
            "risk_flags": [],
        }
        content = (
            "<|channel|>analysis<|message|>internal reasoning"
            "<|channel|>final<|message|>"
            + json.dumps(payload)
        )
        self.assertEqual(agent._parse_structured_content(content, "risk"), payload)

    def test_parse_structured_content_rejects_wrong_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "required JSON object"):
            agent._parse_structured_content('{"answer": 42}', "risk")

    def test_run_agent_uses_fixed_model_and_json_schema(self) -> None:
        response = {
            "id": "test-response",
            "model": "openai/gpt-oss-20b:free",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "department": "risk",
                                "source_version": "v2",
                                "scenario_id": "base_case",
                                "risk_flags": [],
                            }
                        )
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8},
        }
        captured: dict = {}

        def fake_request(endpoint, headers, body, **kwargs):
            captured["endpoint"] = endpoint
            captured["headers"] = headers
            captured["body"] = body
            return response

        request_payload = {
            "department": "risk",
            "system_prompt": "system",
            "user_prompt": "user",
        }
        env = {
            "OPENROUTER_API_KEY": "secret-test-key",
            "OPENROUTER_MODEL": "openai/gpt-oss-20b:free",
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            agent, "_request_json", side_effect=fake_request
        ):
            result = agent.run_agent(request_payload)

        self.assertEqual(
            captured["endpoint"], "https://openrouter.ai/api/v1/chat/completions"
        )
        self.assertEqual(
            captured["body"]["model"], "openai/gpt-oss-20b:free"
        )
        self.assertEqual(
            captured["body"]["response_format"]["type"], "json_schema"
        )
        self.assertTrue(captured["body"]["provider"]["require_parameters"])
        self.assertNotIn("secret-test-key", json.dumps(result))
        self.assertEqual(result["input_tokens"], 12)
        self.assertEqual(result["output_tokens"], 8)

    def test_missing_key_is_rejected(self) -> None:
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "Missing OPENROUTER_API_KEY"):
                agent.run_agent(
                    {
                        "department": "risk",
                        "system_prompt": "system",
                        "user_prompt": "user",
                    }
                )


if __name__ == "__main__":
    unittest.main()
