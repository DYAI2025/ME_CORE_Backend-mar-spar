"""Activation operator helpers for marker evaluation."""
from __future__ import annotations

from typing import Iterable


def any_operator(count: int, threshold: int) -> bool:
    """Return True if at least ``threshold`` events occurred."""
    return count >= threshold


def all_operator(count: int, threshold: int) -> bool:
    """Return True if exactly ``threshold`` events occurred."""
    return count == threshold


def sum_operator(weights: Iterable[float], threshold: float) -> bool:
    """Return True if the sum of ``weights`` meets ``threshold``."""
    return sum(weights) >= threshold

OPERATORS = {
    "ANY": any_operator,
    "ALL": all_operator,
    "SUM": sum_operator,
}
