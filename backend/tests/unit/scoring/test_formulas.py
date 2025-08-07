import math
import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from detect.scoring.SCR_score_models import logistic, linear, step


def test_logistic_extremes():
    assert logistic(-10, 1) < 0.1
    assert logistic(0, 1) == pytest.approx(0.5, rel=1e-3)
    assert logistic(10, 1) > 0.9


def test_linear():
    assert linear(5, 0) == 5


def test_step_threshold():
    assert step(2, 5) == 0.0
    assert step(5, 5) == 1.0
    assert step(7, 5) == 1.0

