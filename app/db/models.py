"""
TREMOR — SQLAlchemy models.

Schema must be Postgres-compatible (use types that work on both SQLite and PG).

Owner: Kostubh (Phase 3)
"""

from __future__ import annotations

# TODO: Implement in Phase 3
# Key models:
#   class AlertRecord(Base):
#       __tablename__ = "alerts"
#       id, service, signal_type, status, severity,
#       explanation (JSON), timeline (JSON), samples (JSON),
#       created_at, updated_at, resolved_at
#
#   class DeliveryRecord(Base):
#       __tablename__ = "deliveries"
#       id, alert_id, sink_name, status, attempted_at, error_message
