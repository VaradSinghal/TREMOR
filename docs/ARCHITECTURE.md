# TREMOR — Architecture

> **T**rend-aware **R**eal-time **E**vent **M**onitoring & **O**utlier **R**esponse

## System Overview

```
                 ┌────────────────────────── TREMOR (FastAPI process) ───────────────────────────┐
                 │                                                                                │
 app.log ──────► │ Tailer ─► Parser ─► Template Miner ─► Window Engine ─► Baseline Store          │
 (growing,       │ (rotation- (regex/   (drain3)          (1s buckets;      (per service,        │
  rotating)      │  safe)     JSON)                        10s/1m/5m views)  hour-of-day, frozen  │
                 │                                                          during anomalies)     │
                 │                                                   │                            │
                 │                    Detector Suite ◄───────────────┘                            │
                 │     (error-rate · traffic-silence · new-pattern · latency)                     │
                 │                          │                                                     │
                 │                Alert Manager (dedup, severity, lifecycle, cooldown, silences)  │
                 │            ┌─────────────┼───────────────────┬───────────────┐                 │
                 │        SQLite/PG     WebSocket hub     CloudWatch Logs     SNS (+ metric)      │
                 └────────────┼─────────────┼───────────────────┼───────────────┼─────────────────┘
                              │             ▼                   ▼               ▼
                          History API   React dashboard   Log group        Email/SMS/Lambda
```

## Design Principles

1. **Event time, not wall time.** Windows advance on log timestamps with a small lateness tolerance (5s default).
2. **Injectable clock everywhere.** No direct `time.time()` in `core/`. Tests are deterministic.
3. **Detection never blocks on I/O.** Sinks are queue-fed background workers.
4. **Everything explainable.** Every alert stores the numbers that caused it.
5. **Graceful degradation.** AWS down, DB slow, or WS dropped: the detector keeps running.

## Component Details

_To be completed as each phase is implemented._

## Data Flow

_To be completed in Phase 3._
