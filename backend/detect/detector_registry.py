"""Utility functions for working with the detector registry.

The project previously expected a file named ``detector_registry.json``.  The
repository however contained ``DETECT_registry.json`` which caused the loader
to fail.  This module provides a tiny API used by the dashboard and other
components to read and write the registry in a consistent way.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import jsonschema


# Path to the registry JSON file relative to this module
REGISTRY_PATH = Path(__file__).resolve().parent / "detector_registry.json"
# JSON schema used for validation
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "tools" / "detector-schema.json"


def load_registry() -> List[Dict[str, Any]]:
    """Load and return the detector registry."""

    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def persist_registry(registry: List[Dict[str, Any]]) -> None:
    """Persist a new detector registry to disk."""

    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def validate_registry(registry: List[Dict[str, Any]]) -> List[str]:
    """Validate registry structure using the bundled JSON schema."""

    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = jsonschema.Draft7Validator(schema)
    return [e.message for e in validator.iter_errors(registry)]

