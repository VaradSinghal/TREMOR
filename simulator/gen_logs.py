"""
TREMOR — Log generator.

Generates realistic fintech log lines and appends them to the monitored file.
Supports multiple services: payment-gateway, auth-service, ledger.
Uses Poisson arrivals, configurable baseline error rate (1-3%), hour-of-day patterns.

Scenarios are seeded and reproducible.

Owner: Mokshad (Phase 1 for steady, Phase 6 for all scenarios)
"""

from __future__ import annotations

# TODO: Implement
# Key interfaces:
#   class LogGenerator:
#       def __init__(self, seed: int, output_path: str): ...
#       async def run_scenario(self, scenario: Scenario) -> None: ...
#       def generate_line(self, service, level, template) -> str: ...
