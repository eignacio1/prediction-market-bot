"""Runtime run-provenance capture (GG-302 remediation). PAPER/DEMO ONLY.

Every position row and audit event a run writes must be attributable to an
actor: which code, which trigger, which run, which host. `logic_epoch`'s
`CURRENT_APPROVAL_COMMIT` cannot do this -- it is `_BOUNDARIES[-1].commit_sha`,
a static epoch marker baked into the source tree, so it is identical for every
run of every checkout at that epoch and identifies nothing about a run.

DESIGN CHOICE: `approval_commit` is left exactly as-is (backfill, band monitor
and replay tooling read it as an epoch marker). This module adds DISTINCT
runtime fields beside it. Nothing here changes what `approval_commit` means.

Trigger attestation: a process cannot reliably self-detect "cron". cron and a
detached ssh/nohup hand-run look alike (no tty). So the trigger is ATTESTED,
not inferred: a scheduled entry must set PMBOT_RUN_TRIGGER=cron in its
environment; anything else is recorded as "manual" (the safe default -- an
unattested run is never presented as scheduled). Environment evidence
(tty, ssh) is captured beside it so a false "cron" attestation is checkable.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

TRIGGER_ENV = "PMBOT_RUN_TRIGGER"
VALID_TRIGGERS = ("cron", "manual")
UNKNOWN = "UNKNOWN"


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def capture_run_provenance(
    *,
    run_id: str | None = None,
    code_root: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Capture provenance AT RUNTIME. Never raises; unknowns are the literal
    "UNKNOWN", never blank and never a static marker."""
    env = os.environ if env is None else env
    root = Path(code_root) if code_root else Path(__file__).resolve().parent
    sha = _git(["rev-parse", "HEAD"], root)
    porcelain = _git(["status", "--porcelain", "--untracked-files=no"], root)
    raw_trigger = (env.get(TRIGGER_ENV) or "").strip().lower()
    trigger = raw_trigger if raw_trigger in VALID_TRIGGERS else "manual"
    try:
        tty = bool(sys.stdin.isatty())
    except (AttributeError, ValueError):
        tty = False
    return {
        "runtime_git_sha": sha or UNKNOWN,
        "runtime_git_dirty": (bool(porcelain) if porcelain is not None else None),
        "run_trigger": trigger,
        "run_trigger_attested": raw_trigger in VALID_TRIGGERS,
        "run_id": run_id or f"RUN-{uuid.uuid4().hex[:12].upper()}",
        "run_host": socket.gethostname() or UNKNOWN,
        "run_started_at": datetime.now(timezone.utc).isoformat(),
        "run_pid": os.getpid(),
        "run_env_evidence": {
            "stdin_tty": tty,
            "ssh_connection": bool(env.get("SSH_CONNECTION")),
        },
    }


class ProvenanceAuditLogger(AuditLogger):
    """AuditLogger that stamps `payload["run_provenance"]` on EVERY event,
    including events emitted by RiskEngine/PaperTrader, which hold this logger
    and know nothing about provenance."""

    def __init__(self, log_path: str | Path, provenance: dict[str, Any], **kw: Any) -> None:
        super().__init__(log_path, **kw)
        self._provenance = dict(provenance)

    def log(self, component, event_type, payload=None, *args, **kwargs):  # type: ignore[override]
        merged = {**(payload or {}), "run_provenance": self._provenance}
        return super().log(component, event_type, merged, *args, **kwargs)
