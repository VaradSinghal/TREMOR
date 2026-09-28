"""
TREMOR — Traffic silence detector.

Responsibilities:
- Fire when volume drops below a fraction of baseline (default 20%)
- Fire when no lines arrive for SILENCE_SECONDS
- Only fire when baseline volume is meaningful
- A stream going quiet is often worse than errors

Owner: Kostubh (Phase 2)
"""

from __future__ import annotations

# TODO: Implement in Phase 2
