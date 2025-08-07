"""Scoring helper functions used by the detection pipeline.

The original scoring implementation scattered a couple of hard coded
equations throughout the code base.  For the LD 3.2 update we introduce a
pluggable system where the formula can be chosen per marker definition.  Each
function below accepts the raw aggregated value and returns a score between
0.0 and 1.0.
"""

from __future__ import annotations

import math
from typing import Callable, Dict


def logistic(raw: float, k: float) -> float:
    """Logistic transformation of ``raw``.

    Parameters
    ----------
    raw: float
        The aggregated raw value.
    k: float
        Logistic growth constant controlling the slope.
    """

    return 1.0 / (1.0 + math.exp(-k * raw))


def linear(raw: float, *_: float) -> float:
    """Simple linear mapping."""

    return raw


def step(raw: float, threshold: float) -> float:
    """Return ``1`` if ``raw`` is above ``threshold`` else ``0``."""

    return 1.0 if raw >= threshold else 0.0


FORMULAS: Dict[str, Callable[[float, float], float]] = {
    "logistic": logistic,
    "linear": linear,
    "step": step,
}


def apply_formula(raw: float, scoring: Dict[str, float]) -> float:
    """Apply the configured scoring formula.

    Parameters
    ----------
    raw: float
        Aggregated raw score.
    scoring: Dict[str, float]
        Scoring configuration typically coming from a marker definition.  The
        dictionary may contain ``formula`` (str) and optional parameters such as
        ``k`` or ``threshold``.
    """

    formula_name = scoring.get("formula", "linear")
    formula = FORMULAS.get(formula_name, linear)
    param = scoring.get("k") if formula is logistic else scoring.get("threshold", 0)
    return formula(raw, param if param is not None else 0)

