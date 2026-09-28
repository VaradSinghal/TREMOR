"""
TREMOR — Dry-run sink (local log-only).

Responsibilities:
- Log what would be sent (to structlog) without making real AWS calls
- Mark delivery status as DRY_RUN
- Active when DRY_RUN=true
- Enables demo without AWS credentials or network

Owner: Sara (Phase 4)
"""

from __future__ import annotations

# TODO: Implement in Phase 4
