"""
TREMOR — CloudWatch Logs sink.

Responsibilities:
- put_log_events with structured JSON for every alert lifecycle event
- Create log group and stream on startup if missing
- No sequence token needed (modern API)
- Also publishes ErrorRate custom metric via put_metric_data

Owner: Sara (Phase 4)
"""

from __future__ import annotations

# TODO: Implement in Phase 4
