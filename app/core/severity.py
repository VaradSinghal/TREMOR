"""
TREMOR — Severity scoring engine.

Severity levels:
- INFO:     z >= 2
- WARNING:  z >= 3 for 2+ consecutive windows
- HIGH:     z >= 4, or rate > 2x baseline sustained
- CRITICAL: z >= 6, or rate above hard ceiling (50%), or silence on critical service

Computed from z-score, sustained duration, and absolute ceiling.
Escalate immediately on worsening. De-escalate only after hysteresis.

Owner: Kostubh (Phase 2)
"""

from __future__ import annotations

from enum import IntEnum


class Severity(IntEnum):
    """Alert severity levels, ordered for comparison."""

    INFO = 1
    WARNING = 2
    HIGH = 3
    CRITICAL = 4


# TODO: Implement in Phase 2
# Key interfaces:
#   def compute_severity(z: float, consecutive: int, rate: float, settings: Settings) -> Severity
#   def should_escalate(current: Severity, new: Severity) -> bool
#   def should_deescalate(current: Severity, new: Severity, clear_count: int) -> bool
