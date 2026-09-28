"""
TREMOR — Error-rate anomaly detector.

Responsibilities:
- z = (rate - baseline.mean) / sigma_eff
- Guards: MIN_EVENTS per window, absolute rate floor
- Consecutive-window confirmation
- Hysteresis: raise at z >= 3, clear only after z < 1.5 for 3 consecutive windows
- Runs on all three window sizes (10s, 60s, 300s)

Owner: Kostubh (Phase 2)
"""

from __future__ import annotations

# TODO: Implement in Phase 2
