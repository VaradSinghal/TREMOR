"""
TREMOR — Sink base protocol and queue worker.

Responsibilities:
- Sink protocol: async send(alert_event) -> DeliveryStatus
- Queue worker: consume from bounded asyncio.Queue
- Retry with exponential backoff + jitter via tenacity
- Circuit breaker: stop trying after N consecutive failures, auto-recover
- Delivery status written back to alert record

Owner: Sara (Phase 4)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol


class DeliveryStatus(StrEnum):
    """Status of a sink delivery attempt."""

    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    DRY_RUN = "DRY_RUN"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"


class Sink(Protocol):
    """Protocol for alert sinks."""

    @property
    def name(self) -> str:
        """Human-readable sink name."""
        ...

    async def send(self, event: dict) -> DeliveryStatus:
        """Send an alert event. Must not raise — return status instead."""
        ...

    async def close(self) -> None:
        """Graceful shutdown — flush pending work."""
        ...


# TODO: Implement in Phase 4
# Key interfaces:
#   class SinkWorker:
#       def __init__(self, sink: Sink, queue_size: int): ...
#       async def enqueue(self, event: dict) -> None: ...
#       async def run(self) -> None: ...
#       async def stop(self) -> None: ...
