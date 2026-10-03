from __future__ import annotations

import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[1]
CONTRACTS = ROOT / "contracts"

FILES = {
    "snapshot": "coordination-snapshot-v0.1.schema.json",
    "scenario": "scenario-definition-v0.1.schema.json",
    "result": "scenario-result-v0.1.schema.json",
    "web_summary": "web-scenario-summary-v0.1.schema.json",
}

def validate(kind: str, payload: dict) -> None:
    schema = json.loads((CONTRACTS / FILES[kind]).read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
