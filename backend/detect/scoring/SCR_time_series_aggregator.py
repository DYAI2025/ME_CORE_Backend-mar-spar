"""Time series aggregation utilities used by the scoring pipeline.

This module provides a minimal implementation of the aggregation behaviour
needed for the LD 3.2 upgrade.  It respects the ``window`` configuration from
the marker definition and performs a decay pass after scoring.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, Iterable, Any

import json
from pathlib import Path

from .SCR_score_models import apply_formula

# Load default scoring configuration
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "default_config.json"
with DEFAULT_CONFIG_PATH.open("r", encoding="utf-8") as _cfg:
    DEFAULT_CONFIG = json.load(_cfg)


def aggregate_events(marker: Dict[str, Any], events: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate event scores for a marker.

    Parameters
    ----------
    marker: dict
        Marker definition containing ``window`` and ``scoring`` blocks.
    events: iterable of dict
        Events must provide ``timestamp`` (epoch seconds) and ``value``.
    """

    events = list(events)
    if not events:
        return {"raw_score": 0.0, "score": 0.0}

    window = marker.get("window", {})

    # Global window overrides from config based on marker type
    marker_id = marker.get("id", "")
    type_map = {"A": "ATO", "S": "SEM", "C": "CLU", "MM": "MEMA"}
    marker_type = ""
    if marker_id.startswith("MM"):
        marker_type = "MEMA"
    elif marker_id:
        marker_type = type_map.get(marker_id[0], "")

    defaults = DEFAULT_CONFIG.get("windows", {}).get(marker_type, {})

    messages = window.get("messages", defaults.get("messages"))
    seconds = window.get("seconds", defaults.get("seconds"))

    # Apply simple window filter: keep last ``messages`` events and those within
    # ``seconds`` seconds from now.  The implementation is intentionally light
    # weight – the tests cover the expected behaviour.
    now = datetime.utcnow().timestamp()
    filtered = events
    if messages is not None:
        filtered = filtered[-messages:]
    if seconds is not None:
        threshold = now - seconds
        filtered = [e for e in filtered if e["timestamp"] >= threshold]

    total_weight = sum(e.get("weight", e.get("value", 0.0)) for e in filtered)

    scoring = {**DEFAULT_CONFIG, **marker.get("scoring", {})}
    threshold = scoring.get("threshold", 1.0)
    base = scoring.get("base", 1.0)
    weight_factor = scoring.get("weight", 1.0)
    raw_score = (total_weight / threshold) * base * weight_factor

    score = apply_formula(raw_score, scoring)

    # Decay pass
    decay = scoring.get("decay")
    if decay:
        last_ts = max(e["timestamp"] for e in filtered)
        hours_since = (now - last_ts) / 3600.0
        score *= math.exp(-decay * hours_since)

    max_score = scoring.get("max_score")
    if max_score is not None:
        score = min(score, max_score)

    return {"raw_score": raw_score, "score": score}

