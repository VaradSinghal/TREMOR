"""
TREMOR — Evaluation harness.

Usage: python -m eval.run --seed 42

Generates labelled scenarios, replays through the detector with FakeClock.
Reports: precision, recall, F1, mean/median detection delay, false positives/hour.
Compares: TREMOR vs static threshold (5%) vs rolling-mean-only.
Output: markdown table to docs/EVAL.md + console.

Owner: Kostubh (Phase 6)
"""

from __future__ import annotations

# TODO: Implement in Phase 6
# Key interfaces:
#   class EvalHarness:
#       def __init__(self, seed: int): ...
#       def run_scenario(self, scenario, detector_fn) -> EvalResult: ...
#       def compare(self, results: dict[str, EvalResult]) -> str: ...  # markdown table
#
#   @dataclass
#   class EvalResult:
#       precision: float
#       recall: float
#       f1: float
#       mean_delay_s: float
#       median_delay_s: float
#       false_positives_per_hour: float


if __name__ == "__main__":
    print("TREMOR Evaluation Harness — not yet implemented (Phase 6)")
