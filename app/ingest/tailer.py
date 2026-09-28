"""
TREMOR — Async log file tailer.

Responsibilities:
- Async poll loop with configurable interval (default 150ms)
- Detect rotation (inode change) and truncation (size < offset)
- Drain old handle before switching on rotation
- Buffer partial lines until newline arrives
- Tag events with service name (from filename or JSON field)
- Backpressure via bounded asyncio.Queue
- Start position: end (default) or beginning (replay/eval)

Owner: Mokshad (Phase 1)
"""

from __future__ import annotations

# TODO: Implement in Phase 1
# Key interfaces to expose:
#   class Tailer:
#       def __init__(self, path, service, queue, clock, start_pos, poll_ms): ...
#       async def run(self) -> None: ...
#       async def stop(self) -> None: ...
