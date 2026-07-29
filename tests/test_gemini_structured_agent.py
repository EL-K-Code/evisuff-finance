from __future__ import annotations

import unittest

from tools.gemini_structured_agent import (
    DEPARTMENTS,
    FACT_FIELDS,
    METRIC_FIELDS,
    department_schemas,
    response_format,
    response_schema,
)


class GeminiStructuredAgentSchemaTests(unittest.TestCase):
    def test_generalist_schema_contains_exact_department_keys(self) -> None:
        schema = response_schema(None)
        self.assertEqual(set(schema["properties"]), set(DEPARTMENTS))
        self.assertEqual(set(schema["required"]), set(DEPARTMENTS))
        self.assertFalse(schema["additionalProperties"])

    def test_department_schemas_are_closed_objects(self) -> None:
        schemas = department_schemas()
        self.assertEqual(set(schemas), set(DEPARTMENTS))
        for name, schema in schemas.items():
            with self.subTest(department=name):
                self.assertEqual(schema["type"], "object")
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(schema["required"]), set(schema["properties"]))

    def test_financial_fields_are_fully_constrained(self) -> None:
        schemas = department_schemas()
        self.assertEqual(
            set(schemas["diligence"]["properties"]["facts"]["required"]),
            set(FACT_FIELDS),
        )
        self.assertEqual(
            set(schemas["valuation"]["properties"]["outputs"]["required"]),
            set(METRIC_FIELDS),
        )
        self.assertEqual(
            set(schemas["memo"]["properties"]["headline_metrics"]["required"]),
            set(METRIC_FIELDS),
        )

    def test_response_format_routes_to_requested_department(self) -> None:
        generalist = response_format(None)
        self.assertEqual(generalist["type"], "json_schema")
        self.assertEqual(
            generalist["json_schema"]["name"], "ipo_workflow_artifacts"
        )
        for department in DEPARTMENTS:
            with self.subTest(department=department):
                payload = response_format(department)
                self.assertTrue(payload["json_schema"]["strict"])
                self.assertEqual(
                    payload["json_schema"]["schema"], response_schema(department)
                )

    def test_unknown_department_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            response_schema("treasury")


if __name__ == "__main__":
    unittest.main()
