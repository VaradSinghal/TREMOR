"""
TREMOR — Application configuration via pydantic-settings.

All configuration is driven by environment variables with sane defaults.
See .env.example for the full list.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):   
    """Application settings, loaded from environment / .env file."""

    # ── Ingestion ─────────────────────────────────────────────────────
    log_paths: str = "./sample/app.log"
    tail_start: str = "end"  # "end" | "beginning"
    poll_interval_ms: int = 150
    lateness_s: int = 5

    # ── Windows & Baseline ───────────────────────────────────────────
    windows_s: str = "10,60,300"
    warmup_seconds: int = 300
    min_events: int = 20

    # ── Severity Thresholds ──────────────────────────────────────────
    z_info: float = 2.0
    z_warn: float = 3.0
    z_high: float = 4.0
    z_crit: float = 6.0
    rate_ceiling: float = 0.5
    clear_z: float = 1.5
    clear_windows: int = 3

    # ── Silence ──────────────────────────────────────────────────────
    silence_seconds: int = 30

    # ── Alerts ───────────────────────────────────────────────────────
    alert_cooldown_s: int = 300

    # ── AWS ──────────────────────────────────────────────────────────
    sns_topic_arn: str = ""
    cw_log_group: str = "/tremor/alerts"
    cw_log_stream: str = "default"
    cw_namespace: str = "Tremor"
    aws_endpoint_url: str = ""

    # ── Modes ────────────────────────────────────────────────────────
    dry_run: bool = False
    demo_mode: bool = False

    # ── Database ─────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./tremor.db"

    # ── Server ───────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "*"

    # ── Logging ──────────────────────────────────────────────────────
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

    @property
    def window_sizes(self) -> list[int]:
        """Parse WINDOWS_S into a list of integers."""
        return [int(w.strip()) for w in self.windows_s.split(",")]

    @property
    def log_file_paths(self) -> list[str]:
        """Parse LOG_PATHS into a list of file paths."""
        return [p.strip() for p in self.log_paths.split(",")]

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list."""
        return [o.strip() for o in self.cors_origins.split(",")]


# Singleton — import this throughout the app
settings = Settings()
