"""
TREMOR — SNS sink.

Responsibilities:
- Publish HIGH and CRITICAL alerts on open, escalation to CRITICAL, and resolution
- Set MessageAttributes: severity (String), service (String) for subscriber filtering
- Uses asyncio.to_thread for boto3 calls

Owner: Sara (Phase 4)
"""

from __future__ import annotations

# TODO: Implement in Phase 4
