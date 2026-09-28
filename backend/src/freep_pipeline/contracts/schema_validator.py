"""Validates published records against the versioned JSON Schemas in
../../../contracts/ (AC12: "the selected machine-readable interface
validates against a versionable data contract").

The schema files are the single source of truth for what a published
JobRecord/ScanRun looks like — this class just loads and applies them. It
never encodes field rules itself; those live in the schema JSON so the
contract stays declarative and independently readable by the schema
validation step in CI (brief §9.1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema.validators import Draft202012Validator

CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "contracts"
JOB_RECORD_SCHEMA_PATH = CONTRACTS_DIR / "job_record.schema.json"
SCAN_RUN_SCHEMA_PATH = CONTRACTS_DIR / "scan_run.schema.json"


@dataclass
class SchemaValidationResult:
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class SchemaValidator:
    """Loads a JSON Schema once and validates records/reports against it."""

    def __init__(self, schema_path: Path) -> None:
        self._schema_path = schema_path
        self._schema = self._load_schema(schema_path)
        Draft202012Validator.check_schema(self._schema)
        self._validator = Draft202012Validator(self._schema)

    @staticmethod
    def _load_schema(schema_path: Path) -> dict[str, Any]:
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)

    def validate(self, record: dict[str, Any]) -> SchemaValidationResult:
        errors = [
            f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
            for error in sorted(self._validator.iter_errors(record), key=str)
        ]
        return SchemaValidationResult(errors=errors)


def job_record_validator() -> SchemaValidator:
    return SchemaValidator(JOB_RECORD_SCHEMA_PATH)


def scan_run_validator() -> SchemaValidator:
    return SchemaValidator(SCAN_RUN_SCHEMA_PATH)


__all__ = [
    "SchemaValidationResult",
    "SchemaValidator",
    "job_record_validator",
    "scan_run_validator",
]
