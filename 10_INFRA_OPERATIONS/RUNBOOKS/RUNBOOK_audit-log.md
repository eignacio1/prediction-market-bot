# Runbook: Audit Log Corruption / Loss (FM-07, HIGH)

**Purpose:** Diagnose and remediate C6 audit-log write failures, corruption, or gaps — the traceability backbone for every C1–C7 event and the G6 evidence trail.
**Owner (role):** Architecture Owner (AO)
**Last reviewed:** 2026-07-13
**Next review:** On any change to `audit_logger.py`, log rotation policy, or VPS disk provisioning
**Staleness triggers:** New log file path added; disk capacity change on VPS; a real audit-log incident with a cause not covered here
**Upstream links:** `RESILIENCE_FAILURE_MODES.md` (FM-07 definition), NFR-03 (kill switch ≤60s), NFR-05 (secrets redaction)
**Downstream links:** `06_CODE_EXECUTION_REPRODUCIBILITY/DATA_RETENTION_DELETION.md` (CAT-04 retention), `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-092)
**Decision references:** ADR-0001 (Compass OS — C6 always active), ADR-0002 (forecast-only)
**Confidence:** 7/10 — the write-failure code path is directly grounded in `audit_logger.py`; the one substantive open question (whether callers reliably act on a `False` return to actually halt) is called out explicitly below rather than assumed resolved.

---

## Overview

C6 (`src/prediction_market_bot/c6_audit_logger/audit_logger.py`) is the append-only, thread-safe JSON Lines audit log. Per its own module docstring: "C6 is the traceability backbone — a silently failing logger is worse than a halted system." Every C1–C5/C7 component writes through `AuditLogger.log()` (or its `.info()`/`.warning()`/`.error()`/`.critical()` convenience wrappers).

Real log file paths in this system (do not assume a single file):

| File | Bands / source |
|------|------------------|
| `logs/audit.jsonl` | T1/T2/T3 (NBA + MLB), kill-switch state — via `run_add_players.py`, `run_resolve.py`, `run_pregame.py`, `run_paper_trade.py`, `run_t3_pretip.py`, `run_t2_mlb_sameday.py`, `run_exp016.py` |
| `logs/audit_t4.jsonl` | T4 NBA — `run_t4_live.py`, `run_t4_resolve_local.py` |
| `logs/audit_mlb_t4.jsonl` | T4 MLB (T4M-PROJ) — `run_t4_mlb_live.py:167`, `CONTAMINATION_HALT` events |
| `logs/audit_mlb_t4_edge_decisions.jsonl` | T4 MLB C4 edge-decision sink — `run_t4_mlb_live.py:1283` |
| `/opt/prediction-market-bot/logs/audit.jsonl`, `/opt/prediction-market-bot/logs/audit_t4.jsonl` | VPS-side mirrors (same files, absolute paths — referenced by `run_resolve_local.py`/`run_t4_resolve_local.py`'s `VPS_AUDIT` constants) |

`c8_dashboard/dashboard.py` reads all of these for its health panels. Retention (`DATA_RETENTION_DELETION.md` CAT-04): 2-year minimum in ENV-01/02 (current paper-trading phase), 5-year minimum once live capital (ENV-03) is authorized.

Redaction: `_REDACTED_KEYS` (`audit_logger.py:65-77`) — `api_key`, `api_secret`, `venue_api_key`, `venue_api_secret`, `password`, `token`, `secret`, `authorization`, `auth_header` — are recursively redacted from any payload before write, enforcing NFR-05. This runs on every `.log()` call unconditionally; it is not something an incident responder needs to trigger manually.

---

## Trigger Conditions

### Automatic

| Signal | Where | What it means |
|--------|-------|----------------|
| `[C6 AUDIT LOGGER WRITE FAILURE] <exc> — kill switch should be triggered` on stderr | `audit_logger.py:278-281`, raised on `IOError`/`OSError`/`PermissionError` during the `jsonlines.open(..., mode="a")` write | Disk full, permissions issue, or path problem prevented a write. `.log()` returns `False` rather than raising. |
| `.log()`/`.info()`/etc. return `False` | Any caller | The caller received the failure signal — see **Known Gap** below regarding whether every caller actually acts on it |
| Gap in sequential `event_id`s (`EVT-XXXXXXXXXXXX`) within a session | Manual audit | A write silently didn't land even though no exception surfaced up to the operator's console |
| `_chain_warning` field present on a non-DEBUG entry | `audit_logger.py:262-266` | Entry was written but with no traceability anchor (`session_id`/`snapshot_id`/`feature_run_id`/`forecast_id`/`risk_eval_id`/`order_id`) — not a write failure, but a traceability-chain integrity gap worth investigating if seen repeatedly |

### Manual

- VPS disk usage approaching capacity (audit logs grow unboundedly under the append-only + 2-year retention policy; no automatic rotation was found in this codebase as of this writing — see Known Gap below).
- A log rotation tool (`logrotate` or similar) misconfigured to truncate or move a file mid-write.
- VPS process crash mid-write leaving a partial/malformed final JSON line.

---

## Diagnostic Procedure

**Step 1 — Check for the explicit write-failure stderr marker.** ≤5 minutes.
```bash
ssh prediction-market-vps "grep -r 'C6 AUDIT LOGGER WRITE FAILURE' /opt/prediction-market-bot/logs/*.log 2>/dev/null | tail -20"
```
Any hit is a confirmed write failure — proceed to Step 3 (root cause) directly.

**Step 2 — If no explicit marker, check for structural corruption or gaps.** ≤10 minutes.
```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python -c \"
import jsonlines
path = 'logs/audit.jsonl'   # adjust per band under investigation
n_ok, n_bad = 0, 0
with open(path) as f:
    for i, line in enumerate(f, 1):
        try:
            import json; json.loads(line)
            n_ok += 1
        except json.JSONDecodeError:
            n_bad += 1
            print(f'malformed line {i}: {line[:120]!r}')
print(f'ok={n_ok} malformed={n_bad}')
\""
```
A non-zero `n_bad` count confirms structural corruption (most commonly a truncated final line from a crash-mid-write, since each write is a single `jsonlines` append — a crash between opening and closing the file could leave a partial line).

**Step 3 — Root-cause the write failure.** ≤10 minutes.
```bash
ssh prediction-market-vps "df -h /opt/prediction-market-bot/logs && ls -la /opt/prediction-market-bot/logs/*.jsonl && stat /opt/prediction-market-bot/logs/audit.jsonl"
```
Check disk usage (`df -h`), file permissions (should be writable by the user/service account running the cron jobs and `t4-mlb` systemd service), and whether the file itself was unexpectedly replaced (different inode/mtime than expected).

**Step 4 — Check whether the failure actually halted anything.** ≤10 minutes — this is the most important step.
The `audit_logger.py` module docstring states a write failure "must trigger the kill switch," but `.log()` itself does **not** raise or self-trigger anything — it returns `False` and prints to stderr, and relies on the **caller** to check that return value and act. Confirm whether the specific caller that hit this failure actually checked the return value:
```bash
grep -n "ok = self._logger\.\|ok = audit\." src/prediction_market_bot/<the calling script>.py
```
Then trace what that script does with `ok` when it's `False`. As of this writing, several call sites (e.g. `paper_trader.py:786-801`, `run_mlb_paper_trade.py:345,697`) do check the return value and propagate an `all_ok`/`ok` flag upward — but whether every call site in every pipeline actually turns a `False` into a real kill-switch trigger (vs. just logging a local warning and continuing) has not been exhaustively verified as part of this runbook's authoring. **If you find a call site where a `False` return is silently discarded, this is itself an FM-07-adjacent gap — register it in `GOVERNANCE_GAP_LOG.md`.**

**Step 5 — Remediate.**
- **Disk full:** free space or expand the VPS volume; once resolved, `.log()` calls succeed again automatically (no code change needed, no backfill possible for the missed entries — see Known Gap on backfill below).
- **Permissions issue:** correct ownership/mode on the log directory (compare against `deploy/t4-mlb.service`'s `WorkingDirectory=/opt/prediction-market-bot` and the user the systemd unit + cron jobs run as).
- **Structural corruption (malformed line):** do NOT delete or truncate the file — append-only integrity must be preserved per NFR-05/FM-07's own mitigation list. Isolate the malformed line for the incident record, but leave the file as-is; downstream consumers (`dashboard.py`, resolution scripts) should be checked for whether they tolerate a single malformed line gracefully (most JSONL readers do, if read line-by-line with per-line error handling — verify the specific consumer before assuming safety).
- **Kill switch not actually triggered despite a `False` return:** this is a governance gap, not a runtime fix — register in `GOVERNANCE_GAP_LOG.md` and add a T-NNN to close the gap between "should trigger" (docstring) and "does trigger" (actual call-site behavior) for the specific caller found.

**Step 6 — Escalate.**
Any confirmed FM-07 incident is HIGH severity per `RESILIENCE_FAILURE_MODES.md` — register in `GOVERNANCE_GAP_LOG.md` immediately (Hard Rule 7). If the gap affected the period during which a resolved bet was recorded, flag that bet's traceability chain as incomplete for G6 evidence purposes (the audit log, not just the portfolio JSON, is part of the evidentiary record per ADR-0008's "two-level confirmation" framing).

---

## Known Failure Modes

| Failure mode | Cause | Detection signal | Mitigation |
|---|---|---|---|
| Disk full on VPS | Unbounded append-only growth under 2-year retention, no rotation found in codebase | `IOError`/`OSError` on write; stderr marker | Monitor VPS disk usage; **no automated rotation exists as of this writing — see Known Gap** |
| Permissions drift | systemd unit or cron job runs as a different user than expected, or `.env`/log dir ownership changed | `PermissionError` on write | Verify `deploy/t4-mlb.service`'s working directory and process user match the log directory's owner |
| Partial/malformed line from crash mid-write | Process killed (OOM, `systemctl restart`, `RestartPreventExitStatus=143` boundary) between `jsonlines.open` and close | Step 2's JSON-decode audit | Append-only format limits blast radius to the single in-flight line; verify downstream readers tolerate one bad line |
| `False` return silently discarded by a caller | A pipeline script checks the return value locally but doesn't propagate to an actual kill-switch trigger | Step 4's call-site trace | Not yet exhaustively audited across all callers — treat any instance found as a new governance gap, not an already-solved problem |

---

## Known Gaps (surfaced during this runbook's authoring, 2026-07-13)

- **No automated log rotation was found** in `deploy/` or `src/` for the audit JSONL files. Given the 2-year (ENV-01/02) / 5-year (ENV-03) retention requirement, unbounded single-file growth is a plausible future disk-capacity risk, not yet mitigated. Worth a future T-NNN if VPS disk usage trends warrant it.
- **The gap between "write failure must trigger the kill switch" (module docstring) and "does trigger" (actual per-caller behavior)** has not been exhaustively verified across every C1–C5/C7 call site — Step 4 above documents how to check a specific caller, but a full audit across all callers is out of scope for this runbook and would be a reasonable follow-up task.
- **No backfill mechanism exists** for entries lost during a write-failure window — once the failure is resolved, logging resumes from that point forward; the gap itself is permanent. This is inherent to an append-only real-time log and is not something to "fix," but should be understood by whoever investigates a gap (do not assume the missing entries can be reconstructed).

---

## References

- `RESILIENCE_FAILURE_MODES.md` — FM-07 canonical definition
- `src/prediction_market_bot/c6_audit_logger/audit_logger.py` — full implementation, `_REDACTED_KEYS`, write-failure handling (lines 268-282)
- `src/prediction_market_bot/c5_execution/paper_trader.py:786-801` — example caller checking `.log()` return value
- `06_CODE_EXECUTION_REPRODUCIBILITY/DATA_RETENTION_DELETION.md` — CAT-04 retention policy
- `deploy/t4-mlb.service` — systemd unit (working directory, restart policy relevant to crash-mid-write scenarios)
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-092
- `10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md` — kill-switch activation procedure (referenced by `audit_logger.py`'s own docstring)
