"""
TREMOR — Log line parser.

Responsibilities:
- Auto-detect plain text vs JSON lines per line
- Plain text format: 2026-01-01T12:00:00.123Z ERROR service-name msg...
- Output LogEvent(ts, level, service, message, duration_ms|None, raw_len)
- Normalize levels: WARN→WARNING, FATAL/CRITICAL→ERROR
- Malformed lines counted and sampled, never fatal
- Cap message length (default 2 KB)

Owner: Mokshad (Phase 1)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogEvent:
    """Parsed log event — the common currency of the pipeline."""

    ts: float  # Unix timestamp
    level: str  # Normalized: DEBUG, INFO, WARNING, ERROR
    service: str
    message: str
    duration_ms: float | None = None
    raw_len: int = 0


# TODO: Implement in Phase 1
# Key interfaces:
#   def parse_line(raw: str, default_service: str) -> LogEvent | None: ...
#   def normalize_level(level: str) -> str: ...
