"""
TREMOR — WebSocket connection manager.

Responsibilities:
- Broadcast to all connected clients
- Drop slow consumers rather than blocking
- Server heartbeat every 15s
- On connect: snapshot of last 50 alerts + current state
- Message envelope: { "type": "snapshot|metric|alert|alert_update", "ts": ..., "data": {...} }

Owner: Kostubh (Phase 3) / Varad (frontend integration Phase 5)
"""

from __future__ import annotations

# TODO: Implement in Phase 3
