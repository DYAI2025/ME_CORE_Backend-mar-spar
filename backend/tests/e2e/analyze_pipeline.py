import time
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[3]))

from detect.detector_registry import load_registry
from detect.scoring.SCR_time_series_aggregator import aggregate_events


def test_simple_pipeline():
    registry = load_registry()
    first = registry[0]
    marker = {
        "id": first["fires_marker"],
        "scoring": {
            "formula": "linear",
            "threshold": 1,
            "base": 1,
            "weight": 1,
            "decay": 0,
        },
    }
    events = [{"timestamp": time.time(), "weight": 1}]
    result = aggregate_events(marker, events)
    assert result["score"] > 0
