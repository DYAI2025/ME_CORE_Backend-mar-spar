import math
import time
import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from detect.scoring.SCR_time_series_aggregator import aggregate_events


def test_window_and_decay():
    now = time.time()
    events = [
        {"timestamp": now - 4000, "weight": 1},  # filtered by seconds
        {"timestamp": now - 30, "weight": 1},
        {"timestamp": now - 10, "weight": 1},
    ]

    marker = {
        "id": "A_TEST",
        "window": {"messages": 2, "seconds": 60},
        "scoring": {
            "formula": "linear",
            "decay": 1.0,
            "threshold": 2,
            "base": 1.0,
            "weight": 1.0,
            "max_score": 10,
        },
    }

    result = aggregate_events(marker, events)
    # Only last two events should remain (messages=2 and seconds=60)
    assert result["raw_score"] == 1  # (2/2)*1*1
    # Score should be decayed from last event (10 seconds)
    expected = 1 * math.exp(-1.0 * (10 / 3600))
    assert result["score"] == pytest.approx(expected, rel=1e-3)

