"""
TREMOR — Simulation scenarios.

Each scenario defines: name, duration, services, error rates, event types, labels.
Scenarios: steady, drift, burst, outage, silence, new_pattern, latency_spike,
           noisy_normal, rotation, malformed_flood

All scenarios are seeded for reproducibility.

Owner: Mokshad (Phase 6)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scenario:
    """Definition of a simulation scenario."""

    name: str
    description: str
    duration_s: int
    seed: int
    # Labels for eval harness: list of (start_s, end_s, signal_type)
    expected_anomalies: list[tuple[float, float, str]]


# Pre-defined scenarios
SCENARIOS: dict[str, Scenario] = {
    "steady": Scenario(
        name="steady",
        description="Normal traffic with ~2% error rate, no anomalies expected",
        duration_s=600,
        seed=42,
        expected_anomalies=[],
    ),
    "drift": Scenario(
        name="drift",
        description="Gradual error rate increase from 2% to 15% over 5 minutes",
        duration_s=600,
        seed=43,
        expected_anomalies=[(180.0, 600.0, "ERROR_RATE")],
    ),
    "burst": Scenario(
        name="burst",
        description="Sudden spike to 80% error rate for 30 seconds",
        duration_s=300,
        seed=44,
        expected_anomalies=[(120.0, 150.0, "ERROR_RATE")],
    ),
    "silence": Scenario(
        name="silence",
        description="Traffic drops to zero for 60 seconds",
        duration_s=300,
        seed=45,
        expected_anomalies=[(120.0, 180.0, "SILENCE")],
    ),
    "new_pattern": Scenario(
        name="new_pattern",
        description="New error template appears suddenly",
        duration_s=300,
        seed=46,
        expected_anomalies=[(150.0, 300.0, "NEW_PATTERN")],
    ),
    "latency_spike": Scenario(
        name="latency_spike",
        description="p95 latency jumps from 200ms to 3000ms",
        duration_s=300,
        seed=47,
        expected_anomalies=[(120.0, 240.0, "LATENCY")],
    ),
    "noisy_normal": Scenario(
        name="noisy_normal",
        description="Naturally noisy service at 3% error rate — must NOT alert",
        duration_s=600,
        seed=48,
        expected_anomalies=[],  # Nothing should fire
    ),
    "rotation": Scenario(
        name="rotation",
        description="Log file rotated mid-stream — no data loss expected",
        duration_s=300,
        seed=49,
        expected_anomalies=[],
    ),
    "malformed_flood": Scenario(
        name="malformed_flood",
        description="50% of lines are malformed — parser must survive",
        duration_s=300,
        seed=50,
        expected_anomalies=[],
    ),
}
