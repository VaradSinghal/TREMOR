"""
TREMOR — API routes.

Endpoints:
- WS  /ws/alerts              Live alert feed + metrics
- GET  /api/alerts             Alert history (filterable)
- GET  /api/alerts/{id}        Alert detail with timeline
- POST /api/alerts/{id}/ack    Acknowledge alert
- POST /api/alerts/{id}/silence  Silence alert for a duration
- GET  /api/metrics/current    Current window metrics per service
- GET  /api/baseline           Baseline state per service/slot
- GET  /api/templates          Top templates and rarity
- POST /api/sim/inject         Demo-only scenario injection
- GET  /health                 Component health status
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["ops"])
async def health() -> dict:
    """Component health check."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "components": {
            "tailer": "not_started",
            "detector": "not_started",
            "sinks": "not_started",
            "database": "not_started",
        },
    }


# ── Alert endpoints (Phase 3) ────────────────────────────────────────

@router.get("/api/alerts", tags=["alerts"])
async def list_alerts() -> dict:
    """List alerts with optional filters."""
    # TODO: Implement in Phase 3 (Kostubh)
    return {"alerts": [], "total": 0}


@router.get("/api/alerts/{alert_id}", tags=["alerts"])
async def get_alert(alert_id: str) -> dict:
    """Get alert detail with timeline and explanation."""
    # TODO: Implement in Phase 3 (Kostubh)
    return {"error": "not_implemented"}


@router.post("/api/alerts/{alert_id}/ack", tags=["alerts"])
async def ack_alert(alert_id: str) -> dict:
    """Acknowledge an alert."""
    # TODO: Implement in Phase 3 (Kostubh)
    return {"error": "not_implemented"}


@router.post("/api/alerts/{alert_id}/silence", tags=["alerts"])
async def silence_alert(alert_id: str) -> dict:
    """Silence an alert for a specified duration."""
    # TODO: Implement in Phase 3 (Kostubh)
    return {"error": "not_implemented"}


# ── Metrics / State endpoints (Phase 3) ──────────────────────────────

@router.get("/api/metrics/current", tags=["metrics"])
async def current_metrics() -> dict:
    """Current window metrics per service (polling fallback)."""
    # TODO: Implement in Phase 3 (Kostubh)
    return {"services": {}}


@router.get("/api/baseline", tags=["metrics"])
async def baseline_state() -> dict:
    """Baseline state per service/slot."""
    # TODO: Implement in Phase 3 (Kostubh)
    return {"baselines": {}}


@router.get("/api/templates", tags=["metrics"])
async def templates() -> dict:
    """Top templates and rarity."""
    # TODO: Implement in Phase 3 (Mokshad/Kostubh)
    return {"templates": []}


# ── Demo endpoint (Phase 5) ──────────────────────────────────────────

@router.post("/api/sim/inject", tags=["demo"])
async def inject_scenario() -> dict:
    """Inject a scenario (demo mode only)."""
    # TODO: Implement in Phase 5 (Varad)
    return {"error": "demo_mode_disabled"}
