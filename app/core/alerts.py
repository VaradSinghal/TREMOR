"""
TREMOR — Alert lifecycle manager.

Responsibilities:
- Alert states: OPEN → ESCALATED → ACKED | SILENCED → RESOLVED
- Dedup key: (service, signal_type) — one spike = one alert with updates
- Cooldown per key to prevent notification spam
- Timeline: opened, escalated, notified, acked, resolved with timestamps
- Ack / Silence (for a duration) from UI
- Root-cause hint: top offending templates + sample lines
- Explainability payload on every alert

Owner: Kostubh (Phase 3)
"""

from __future__ import annotations

from enum import StrEnum


class AlertStatus(StrEnum):
    """Alert lifecycle states."""

    OPEN = "OPEN"
    ESCALATED = "ESCALATED"
    ACKED = "ACKED"
    SILENCED = "SILENCED"
    RESOLVED = "RESOLVED"


class SignalType(StrEnum):
    """Types of anomaly signals."""

    ERROR_RATE = "ERROR_RATE"
    SILENCE = "SILENCE"
    NEW_PATTERN = "NEW_PATTERN"
    LATENCY = "LATENCY"


# TODO: Implement in Phase 3
# Key interfaces:
#   @dataclass
#   class Alert:
#       id: str
#       service: str
#       signal_type: SignalType
#       status: AlertStatus
#       severity: Severity
#       explanation: dict
#       timeline: list[TimelineEvent]
#       samples: list[str]
#       top_templates: list[TemplateHint]
#       created_at: float
#       updated_at: float
#
#   class AlertManager:
#       def __init__(self, clock, cooldown_s): ...
#       def process_signal(self, signal) -> Alert | None: ...
#       def ack(self, alert_id) -> Alert: ...
#       def silence(self, alert_id, duration_s) -> Alert: ...
#       def resolve(self, service, signal_type) -> Alert | None: ...
#       def get_active(self) -> list[Alert]: ...
