"""Utility helpers for loading the detector registry.

This is a thin wrapper around the JSON registry file.  Keeping the logic in a
dedicated module makes it reusable by APIs and tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import jsonschema


REGISTRY_PATH = Path(__file__).resolve().parent / "detector_registry.json"
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "detector-schema.json"


def load_registry() -> List[Dict[str, Any]]:
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def persist_registry(registry: List[Dict[str, Any]]) -> None:
    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def validate_registry(registry: List[Dict[str, Any]]) -> List[str]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = jsonschema.Draft7Validator(schema)
    return [e.message for e in validator.iter_errors(registry)]

