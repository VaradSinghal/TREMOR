"""
TREMOR — FastAPI application factory with lifespan management.

Entry point: `uvicorn app.main:create_app --factory`
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.config import settings


def _configure_logging() -> None:
    """Configure structlog for JSON output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if settings.log_level == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Startup: initialize DB, sinks, tailer, baseline restore.
    Shutdown: stop tailer, flush sinks, persist baseline.
    """
    log = structlog.get_logger()
    await log.ainfo("tremor.starting", version="0.1.0", demo_mode=settings.demo_mode)

    # TODO (Phase 1+): Initialize components in order:
    # 1. Database connection
    # 2. Sink workers (CW, SNS, WS hub)
    # 3. Restore baseline state from disk
    # 4. Start tailer (last — so everything is ready to receive events)

    yield

    # Shutdown: reverse order
    await log.ainfo("tremor.shutting_down")
    # TODO: Stop tailer, flush sinks with deadline, persist baseline


def create_app() -> FastAPI:
    """Application factory."""
    _configure_logging()

    app = FastAPI(
        title="TREMOR",
        description="Trend-aware Real-time Event Monitoring & Outlier Response",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Prometheus metrics ────────────────────────────────────────────
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # ── Routers ──────────────────────────────────────────────────────
    from app.api.routes import router as api_router

    app.include_router(api_router)

    return app
