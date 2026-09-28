"""
TREMOR — Tests for the eval baseline detectors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.ingest.parser import LogEvent
from eval.detectors import (
    DETECTORS,
    RollingMeanDetector,
    StaticThresholdDetector,
    TremorDetector,
)

if TYPE_CHECKING:
    from eval.metrics import EvalAlert

T0 = 1_000_000.0


def feed_second(
    det: StaticThresholdDetector | RollingMeanDetector,
    second: int,
    errors: int,
    lines: int = 10,
    service: str = "svc",
) -> list[EvalAlert]:
    """``lines`` lines in second ``second`` (``errors`` of them ERROR), then tick."""
    for i in range(lines):
        level = "ERROR" if i < errors else "INFO"
        arrival = T0 + second + i / lines
        det.observe(LogEvent(ts=arrival, level=level, service=service, message="m"), arrival)
    return det.tick(T0 + second + 1)


def test_static_threshold_opens_once_and_resolves() -> None:
    det = StaticThresholdDetector()
    alerts: list[EvalAlert] = []
    for s in range(60):  # 0% errors: never fires
        alerts += feed_second(det, s, errors=0)
    assert alerts == []
    for s in range(60, 90):  # 20% errors: opens once, then stays open
        alerts += feed_second(det, s, errors=2)
    assert len(alerts) == 1
    assert alerts[0].signal_type == "ERROR_RATE" and alerts[0].service == "svc"
    for s in range(90, 150):  # back to 0%: the 30 s window drains, then 10 clear ticks
        alerts += feed_second(det, s, errors=0)
    for s in range(150, 160):  # fires again: a new incident
        alerts += feed_second(det, s, errors=5)
    assert len(alerts) == 2


def test_static_threshold_needs_min_events() -> None:
    det = StaticThresholdDetector(min_events=20)
    alerts: list[EvalAlert] = []
    for s in range(5):  # 1 line/s: at most 5 lines in the window
        alerts += feed_second(det, s, errors=1, lines=1)
    assert alerts == []


def test_static_threshold_is_per_service() -> None:
    det = StaticThresholdDetector()
    alerts: list[EvalAlert] = []
    for s in range(40):
        alerts += feed_second(det, s, errors=0, service="quiet")
        alerts += feed_second(det, s, errors=3, service="loud")
    assert [a.service for a in alerts] == ["loud"]


def test_rolling_mean_fires_on_step_not_on_steady() -> None:
    det = RollingMeanDetector(min_history=60)
    alerts: list[EvalAlert] = []
    for s in range(200):  # 10% steady: the mean settles at 10%
        alerts += feed_second(det, s, errors=1)
    assert alerts == []
    for s in range(200, 240):  # 50% is well above 2x the mean
        alerts += feed_second(det, s, errors=5)
    assert len(alerts) == 1


def test_rolling_mean_waits_for_history() -> None:
    det = RollingMeanDetector(min_history=60)
    alerts: list[EvalAlert] = []
    for s in range(30):  # would fire, but there is no history yet
        alerts += feed_second(det, s, errors=9)
    assert alerts == []


def test_tremor_adapter_is_stubbed_until_engine_lands() -> None:
    try:
        import app.core.engine  # noqa: F401
    except ImportError:
        with pytest.raises(NotImplementedError):
            TremorDetector()
    else:  # pragma: no cover - once Kostubh's engine is merged
        pytest.skip("engine merged; covered by eval run tests")


def test_detector_registry() -> None:
    assert list(DETECTORS) == ["TREMOR", "Static 5%", "Rolling mean"]
