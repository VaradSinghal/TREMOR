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


from dataclasses import dataclass, field
from typing import Any

@dataclass
class TemplateHint:
    template_id: int
    pattern: str
    count: int

@dataclass
class TimelineEvent:
    ts: float
    status: AlertStatus
    reason: str

@dataclass
class Alert:
    id: str
    service: str
    signal_type: SignalType
    status: AlertStatus
    severity: str
    explanation: dict[str, Any] = field(default_factory=dict)
    timeline: list[TimelineEvent] = field(default_factory=list)
    samples: list[str] = field(default_factory=list)
    top_templates: list[TemplateHint] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "service": self.service,
            "signal_type": self.signal_type.value,
            "status": self.status.value,
            "severity": self.severity,
            "explanation": self.explanation,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

# TODO: Implement in Phase 3
# Key interfaces:
#   class AlertManager:
#       def __init__(self, clock, cooldown_s): ...
#       def process_signal(self, signal) -> Alert | None: ...
#       def ack(self, alert_id) -> Alert: ...
#       def silence(self, alert_id, duration_s) -> Alert: ...
#       def resolve(self, service, signal_type) -> Alert | None: ...
#       def get_active(self) -> list[Alert]: ...
