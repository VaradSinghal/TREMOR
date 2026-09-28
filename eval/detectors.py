"""
TREMOR — Detectors compared by the eval harness, behind one interface.

Every detector is driven like Kostubh's ``DetectionEngine``: ``observe()`` once per
parsed line with its arrival time, and ``tick(now)`` once per second. ``tick``
returns the alerts *opened* on that tick. Nothing here reads a clock.

- ``StaticThresholdDetector``: fires ERROR_RATE when a service's error rate over
  the last 30 s is above a fixed 5%.
- ``RollingMeanDetector``: fires ERROR_RATE when the rate exceeds twice its own
  rolling mean. There is no seasonality, no spread estimate and no baseline
  freeze, so a slow drift gets absorbed into the mean.
- ``TremorDetector``: adapter for ``app.core.engine.DetectionEngine``. It raises
  ``NotImplementedError`` until Kostubh's engine is merged.

Both baselines cover ERROR_RATE only. Eval reports an ERROR_RATE-only table so
they are compared fairly.

Owner: Mokshad (Phase 6)
"""

from __future__ import annotations

import importlib
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from eval.metrics import EvalAlert

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.ingest.parser import LogEvent

ERROR_RATE = "ERROR_RATE"
WINDOW_S = 30.0  # same arrival window as TREMOR's detectors
MIN_EVENTS = 20
CLEAR_TICKS = 10  # same as TREMOR's clear_windows


class EvalDetector(Protocol):
    """What the harness drives. Construct a fresh instance per scenario."""

    name: str

    def observe(
        self,
        event: LogEvent,
        arrival: float,
        template_id: str | None = None,
        is_new_template: bool = False,
    ) -> None:
        """Record one parsed line that arrived at ``arrival``."""
        ...

    def tick(self, now: float) -> list[EvalAlert]:
        """Evaluate the second ending at ``now``; return alerts opened on this tick."""
        ...


class _ArrivalWindow:
    """Per-service (arrival, is_error) pairs for lines that arrived in ``(now - w, now]``."""

    def __init__(self, window_s: float = WINDOW_S) -> None:
        self._window_s = window_s
        self._lines: dict[str, deque[tuple[float, bool]]] = {}

    def add(self, service: str, arrival: float, is_error: bool) -> None:
        self._lines.setdefault(service, deque()).append((arrival, is_error))

    def advance(self, now: float) -> None:
        cutoff = now - self._window_s
        for lines in self._lines.values():
            while lines and lines[0][0] <= cutoff:
                lines.popleft()

    def services(self) -> list[str]:
        return sorted(self._lines)

    def counts(self, service: str) -> tuple[int, int]:
        """(lines, errors) in the current window."""
        lines = self._lines.get(service, deque())
        return len(lines), sum(1 for _, err in lines if err)


@dataclass(slots=True)
class _Incident:
    open: bool = False
    clear_ticks: int = 0


class _Incidents:
    """Open on the first firing tick; resolve after ``clear_ticks`` quiet ticks in a row."""

    def __init__(self, clear_ticks: int = CLEAR_TICKS) -> None:
        self._clear_ticks = clear_ticks
        self._state: dict[tuple[str, str], _Incident] = {}

    def update(self, service: str, signal_type: str, firing: bool, now: float) -> EvalAlert | None:
        state = self._state.setdefault((service, signal_type), _Incident())
        if firing:
            state.clear_ticks = 0
            if not state.open:
                state.open = True
                return EvalAlert(ts=now, signal_type=signal_type, service=service)
        elif state.open:
            state.clear_ticks += 1
            if state.clear_ticks >= self._clear_ticks:
                state.open = False
                state.clear_ticks = 0
        return None


class StaticThresholdDetector:
    """ERROR_RATE when errors / lines over the last 30 s exceed a fixed threshold."""

    name = "Static 5%"

    def __init__(self, threshold: float = 0.05, min_events: int = MIN_EVENTS) -> None:
        self._threshold = threshold
        self._min_events = min_events
        self._window = _ArrivalWindow()
        self._incidents = _Incidents()

    def observe(
        self,
        event: LogEvent,
        arrival: float,
        template_id: str | None = None,
        is_new_template: bool = False,
    ) -> None:
        """Record one line."""
        self._window.add(event.service, arrival, event.level == "ERROR")

    def tick(self, now: float) -> list[EvalAlert]:
        """Fire per service when the windowed error rate is above the threshold."""
        self._window.advance(now)
        alerts: list[EvalAlert] = []
        for service in self._window.services():
            lines, errors = self._window.counts(service)
            firing = lines >= self._min_events and errors / lines > self._threshold
            alert = self._incidents.update(service, ERROR_RATE, firing, now)
            if alert:
                alerts.append(alert)
        return alerts


class RollingMeanDetector:
    """ERROR_RATE when the rate exceeds ``ratio`` x its own rolling mean (+ a margin)."""

    name = "Rolling mean"

    def __init__(
        self,
        history_ticks: int = 300,
        min_history: int = 60,
        ratio: float = 2.0,
        abs_margin: float = 0.02,
        min_events: int = MIN_EVENTS,
    ) -> None:
        self._history_ticks = history_ticks
        self._min_history = min_history
        self._ratio = ratio
        self._abs_margin = abs_margin
        self._min_events = min_events
        self._window = _ArrivalWindow()
        self._history: dict[str, deque[float]] = {}
        self._incidents = _Incidents()

    def observe(
        self,
        event: LogEvent,
        arrival: float,
        template_id: str | None = None,
        is_new_template: bool = False,
    ) -> None:
        """Record one line."""
        self._window.add(event.service, arrival, event.level == "ERROR")

    def tick(self, now: float) -> list[EvalAlert]:
        """Compare each service's rate with its rolling mean, then fold it into the mean."""
        self._window.advance(now)
        alerts: list[EvalAlert] = []
        for service in self._window.services():
            lines, errors = self._window.counts(service)
            history = self._history.setdefault(service, deque(maxlen=self._history_ticks))
            firing = False
            if lines >= self._min_events:
                rate = errors / lines
                if len(history) >= self._min_history:
                    mean = sum(history) / len(history)
                    firing = rate > max(self._ratio * mean, mean + self._abs_margin)
                history.append(rate)  # no freeze: anomalies leak into the mean
            alert = self._incidents.update(service, ERROR_RATE, firing, now)
            if alert:
                alerts.append(alert)
        return alerts


class TremorDetector:
    """Adapter for Kostubh's ``DetectionEngine`` (see docs/DETECTION_API.md).

    Raises ``NotImplementedError`` while ``app.core.engine`` is not on main, so the
    harness can still run the baselines.
    """

    name = "TREMOR"

    def __init__(self, service: str = "*") -> None:
        try:
            engine_mod = importlib.import_module("app.core.engine")
        except ImportError as exc:
            raise NotImplementedError("app.core.engine.DetectionEngine is not merged yet") from exc
        from app.config import Settings

        self._engine = engine_mod.DetectionEngine(Settings(_env_file=None), service=service)

    def observe(
        self,
        event: LogEvent,
        arrival: float,
        template_id: str | None = None,
        is_new_template: bool = False,
    ) -> None:
        """Forward to ``DetectionEngine.observe``."""
        self._engine.observe(
            event, arrival, template_id=template_id, is_new_template=is_new_template
        )

    def tick(self, now: float) -> list[EvalAlert]:
        """Forward to ``DetectionEngine.tick``; keep only alerts that open an incident."""
        result = self._engine.tick(now)
        return [
            EvalAlert(ts=now, signal_type=str(a.signal_type), service=a.service)
            for a in result.alerts
            if str(a.status) == "OPEN"
        ]


DETECTORS: dict[str, Callable[[], EvalDetector]] = {
    TremorDetector.name: TremorDetector,
    StaticThresholdDetector.name: StaticThresholdDetector,
    RollingMeanDetector.name: RollingMeanDetector,
}
