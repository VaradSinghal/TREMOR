"""
TREMOR — Seasonal robust baseline with freeze logic.

Responsibilities:
- Per (service, hour_of_day_slot) tracking with global fallback
- EWMA mean + median/MAD over rolling history for error-rate, volume, latency p95
- Warm-up: no alerts until WARMUP_SAMPLES seen
- Baseline freeze: do NOT update during active anomaly; resume slowly after resolution
- Sampling-noise aware spread:
    sigma_eff = max(baseline_sigma, sqrt(p0*(1-p0)/n), EPS)
- Persist state to disk on shutdown, restore on start

Owner: Kostubh (Phase 2)
"""

from __future__ import annotations

# TODO: Implement in Phase 2
# Key interfaces:
#   @dataclass
#   class BaselineState:
#       mean: float
#       sigma: float
#       mad: float
#       sample_count: int
#       is_frozen: bool
#
#   class BaselineStore:
#       def __init__(self, clock: Clock, warmup_seconds: int): ...
#       def update(self, service: str, signal: str, value: float, n: int) -> None: ...
#       def get(self, service: str, signal: str) -> BaselineState | None: ...
#       def freeze(self, service: str, signal: str) -> None: ...
#       def unfreeze(self, service: str, signal: str) -> None: ...
#       def is_warm(self, service: str) -> bool: ...
#       async def persist(self, path: str) -> None: ...
#       async def restore(self, path: str) -> None: ...
