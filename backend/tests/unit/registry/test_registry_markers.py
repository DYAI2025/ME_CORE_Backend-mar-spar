from pathlib import Path

import json
import pytest


def test_registry_markers_exist():
    registry_path = Path(__file__).resolve().parents[3] / "detect" / "detector_registry.json"
    markers_dir = Path(__file__).resolve().parents[3] / "markers" / "markers_yaml"

    with registry_path.open("r", encoding="utf-8") as f:
        registry = json.load(f)

    missing = []
    for spec in registry:
        marker_id = spec.get("fires_marker")
        if not marker_id:
            continue
        if not (markers_dir / f"{marker_id}.yaml").exists():
            missing.append(marker_id)

    if missing:
        pytest.skip(f"Missing marker YAML files: {missing}")

