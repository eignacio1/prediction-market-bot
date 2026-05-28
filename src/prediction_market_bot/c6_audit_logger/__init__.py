# C6: Audit Logger
# Phase active: ALWAYS ACTIVE from Phase 3+
# Append-only JSON Lines structured log. NEVER disabled.
# Every event has: timestamp, component, event_type, event_id, session_id, snapshot_id, payload, severity
# Traceability chain: Snapshot ID → Feature run ID → Forecast ID → Risk eval ID → Order ID → Audit entry
# C6 write failure → automatic kill switch trigger
# Retention: 2yr minimum; 5yr if live capital (DATA_RETENTION_DELETION.md CAT-04)
# See: OBSERVABILITY.md, RUNBOOKS/RUNBOOK_kill-switch.md

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

__all__ = ["AuditLogger"]
