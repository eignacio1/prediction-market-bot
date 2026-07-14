# Runbook: Audit Log Corruption / Loss (FM-07, C6)

**Purpose:** Diagnose and recover from missing, corrupted, or unwritten audit log entries. C6 is the traceability backbone — every C1-C5/C7 decision is supposed to be reconstructable from these logs.
**Owner (role):** Infrastructure Operator (IO)
**Last reviewed:** 2026-07-12
**Next review:** If `AuditLogger` gains cross-process locking, or if the kill-switch-on-write-failure contract is ever actually wired up (see the gap documented below)
**Staleness triggers:** New audit log file added for a new band/pipeline; logrotate config change; `AuditLogger` class signature change
**Upstream links:** `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` (FM-07), `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-092)
**Downstream links:** `10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/`
**Decision references:** ADR-0001 (Compass OS, C6 always-active mandate)
**Confidence:** 6/10 — mechanisms verified directly against source; two real gaps documented below are unmitigated as of this writing

---

## Read this first: two real gaps, not just staleness

1. **The documented kill-switch contract is not enforced anywhere.** `audit_logger.py`'s docstring (lines 19-23) states: *"AuditLogger write failure (IOError, PermissionError, disk full) must trigger the kill switch. Downstream callers check the return value."* `AuditLogger.log()` does return `True`/`False` accordingly (line 268-282) and prints to stderr on failure. **But a full-codebase grep for callers checking that return value against `.log(`/`.info(`/`.warning(`/`.error(`/`.critical(`/`.debug(` returns zero hits.** Every call site in `src/` discards the boolean. If a write fails (disk full, permission error), the stderr line is the only signal — nothing wires it to `c7_monitoring/monitor.py`'s actual kill switch (`is_kill_switch_active`, `KILL_SWITCH_SLA_MS = 60_000`). This is a real gap between documented and actual behavior — treat "audit write failure" as **silent** until this is fixed.
2. **"Periodic log integrity check" (the FM-07 canonical mitigation) does not exist.** No hash-chaining, checksum, or dedicated integrity-verification tool was found anywhere in `src/`. There is no code that detects a gap in `event_id` sequence or a truncated file after the fact. Detection today is entirely manual (see Diagnostics).

Both gaps are candidates for their own governance-gap registration if this runbook is ever exercised for a real incident — this runbook documents current reality, it does not fix these gaps.

---

## Overview

`AuditLogger` (`c6_audit_logger/audit_logger.py`) is a thread-safe, append-only JSON Lines writer. Key real properties:
- Append via `jsonlines.open(path, mode="a")` under a `threading.Lock()` — this protects against **in-process** concurrent writes only. It is **not** a cross-process lock (unlike `paper_trader.py`'s `fcntl.flock`-based `_file_lock()`) — two separate processes writing the same audit log file (e.g., a manual re-run overlapping a cron run) are not coordinated by `AuditLogger` itself.
- Auto-redacts a fixed set of sensitive key names (`api_key`, `api_secret`, `password`, `token`, `secret`, `authorization`, etc. — `_REDACTED_KEYS`, line 65) recursively through nested dicts, before write. This is a real, working NFR-05 control — but it only catches known key **names**; a secret logged under an unlisted key name would not be caught (see `RUNBOOK_ingestion-failure.md`/`RUNBOOK_data-contamination.md` style caveat: config, not exhaustive scanning).
- Each entry carries a traceability chain (`session_id → snapshot_id → feature_run_id → forecast_id → risk_eval_id → order_id`); a `_chain_warning` field is added (not a hard failure) if a non-DEBUG event has no chain anchor at all.
- Severity filtering (`min_severity`, default INFO; DEBUG in `BOT_ENV=research`) — sub-threshold events are silently dropped and this counts as a "successful" write (`return True`), not a failure. Do not mistake "fewer entries than expected" for corruption if the run was in a filtered mode.

---

## The Multi-Log Registry — there is no single audit log

**This is not one file.** Every pipeline/band instantiates its own `AuditLogger` against its own path. As of this writing:

| File | Written by | Notes |
|---|---|---|
| `logs/audit_mlb.jsonl` | `run_mlb_paper_trade.py` (T1), `run_mlb_pregame.py`, `run_resolve_mlb.py`, `run_t2_mlb_sameday.py` (T2), `run_t3_mlb_pretip.py` (T3) | **Shared across 5 different pipelines** — a corruption/gap here can mask which band actually failed; always check `component`/`event_type` fields, not just file presence |
| `logs/audit_mlb_edge_decisions.jsonl` | `run_mlb_paper_trade.py` | Separate edge-decision detail log, T1-only |
| `logs/audit_mlb_t4.jsonl` | `run_t4_mlb_live.py` | MLB T4 live-loop log; also the source for the CLAUDE.md `CONTAMINATION_HALT` / `game_state_fresh` health checks |
| `logs/audit_mlb_t4_edge_decisions.jsonl` | `run_t4_mlb_live.py` | Separate edge-decision detail log, T4-MLB-only |
| `logs/audit_t4.jsonl` | `run_t4_live.py` (NBA T4, currently dark) | Dark pipeline — a gap here is not live-risk while NBA is tabled |
| `logs/audit_expNNN.jsonl` (many) | `run_expNNN.py` scripts | Research-only, not production traceability |
| `logs/spread_observations.jsonl`, `logs/t4_position_trajectories.jsonl` | `run_t4_live.py`, raw `open(path, "a")` | **Not written through `AuditLogger` at all** — no redaction, no lock, no severity filtering, no traceability chain. If sensitive data were ever accidentally passed here, the NFR-05 redaction control does not apply. |
| `logs/t4_mlb_cycle_log.jsonl` | `run_t4_mlb_live.py` | Per-cycle counter log (see CLAUDE.md's GG-080 note — `cycle_id` here is a global counter across all concurrently-live games, not per-game) |

**Implication for diagnosis:** "the audit log is fine" must specify *which* audit log. A gap in `audit_mlb_t4.jsonl` says nothing about `audit_mlb.jsonl`'s health, and vice versa.

---

## Trigger Conditions

| Symptom | Likely cause |
|---|---|
| `[C6 AUDIT LOGGER WRITE FAILURE]` on stderr / in cron output | Disk full, permission error, or path issue — `log()` returned `False` but (per the gap above) nothing auto-halted |
| Expected event type absent for a known pipeline run | Either min_severity filtering (check `BOT_ENV`), or a genuine write failure with no downstream alert |
| Sequential `event_id`s show an unexplained gap when manually inspected | Possible partial write, crash mid-write, or `copytruncate` race (see below) |
| VPS disk usage climbing unexpectedly in `logs/` | `rotate 30` (30-day retention) with `compress` — check retention math against `DATA_RETENTION_DELETION.md` CAT-04 (2-year minimum for ENV-01/02) — **the logrotate policy's 30-day local rotation window is far shorter than the 2-year compliance retention requirement; confirm where the 2-year archive actually lives before assuming logrotate alone satisfies it** |

---

## Diagnostics

```bash
# Confirm the audit logger is writing at all (recent timestamp)
ssh prediction-market-vps "tail -3 /opt/prediction-market-bot/logs/audit_mlb.jsonl | python3 -m json.tool 2>&1 | head -20"

# Check for stderr write-failure lines in cron output logs
ssh prediction-market-vps "grep -l 'C6 AUDIT LOGGER WRITE FAILURE' /opt/prediction-market-bot/logs/*.log 2>/dev/null"

# Validate every line is well-formed JSON (crude corruption/truncation check —
# there is no built-in integrity checker, this is the manual substitute)
ssh prediction-market-vps "python3 -c \"
import json
path = '/opt/prediction-market-bot/logs/audit_mlb.jsonl'
bad = 0
with open(path) as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            bad += 1
            print(f'Line {i}: {e}')
print(f'{bad} malformed lines out of {i}')
\""

# Check logrotate state — confirm copytruncate isn't mid-rotation during a write
ssh prediction-market-vps "cat /etc/logrotate.d/pred-market-bot && ls -la /opt/prediction-market-bot/logs/*.jsonl.1 2>/dev/null"

# Check disk space (the most common real trigger for write failures)
ssh prediction-market-vps "df -h /opt/prediction-market-bot"
```

---

## Mitigations

### Mitigation A: Confirmed write failure (disk full / permission error)

1. Free disk space or fix permissions per the stderr message.
2. **Manually verify no kill switch is needed** — since nothing does this automatically (the gap above), you are the enforcement mechanism right now. Check whether the failing pipeline continued placing bets/orders without being able to log them — if so, treat as CRITICAL (an unauditable live decision is a governance-invariant violation per FM-07's own severity rating).
3. Once the underlying cause (disk/permissions) is fixed, confirm the next scheduled run writes successfully (re-run Diagnostics).
4. Register a governance gap for "kill switch not wired to AuditLogger write failure" if not already tracked (see Read-this-first section above) — do not let this recur silently.

### Mitigation B: `copytruncate` data-loss race suspected

`copytruncate` (the configured logrotate strategy, `deploy/setup.sh:65`) copies the file then truncates the original in place — **any write that lands between the copy and the truncate is lost**, and any write in progress exactly at truncation time can be corrupted. This is a known, general `copytruncate` limitation, not specific to this codebase's implementation.
1. Check whether a malformed/truncated line appears near a `.jsonl.1` rotation boundary timestamp (via the Diagnostics JSON-validation script).
2. If found: this is expected, rare-but-real behavior of `copytruncate` under concurrent writes, not a code bug in `AuditLogger`. Document the gap window found; check whether any bet/order decision fell within it (cross-reference `paper_portfolio.json` / `staged_orders*.db` timestamps).
3. A structural fix (switching to non-`copytruncate` rotation with proper `postrotate` signal handling, or moving to a rotation-safe write pattern) is a code/infra change, not something this runbook performs — register a governance gap if this has caused a real gap in traceability.

### Mitigation C: Suspected tampering (modified, not just missing, entries)

There is no hash-chain or signature over entries — **this system currently cannot cryptographically prove an entry hasn't been altered after the fact**, only that its JSON is well-formed. If tampering is suspected (not just accidental loss):
1. Do not rely on the live file alone — check for backups (`.jsonl.N.gz` rotated copies) and compare.
2. Escalate to the operator before drawing conclusions — this is outside what automated diagnostics here can resolve.

---

## Rollback

Audit logs are append-only by design; there is no "rollback" of a corrupted log entry. Recovery means either (a) restoring from a rotated/compressed backup if the live file was damaged, or (b) reconstructing what's reconstructable from other authoritative sources (`paper_portfolio.json`, `staged_orders*.db`, cron stdout logs) and documenting the gap explicitly rather than silently patching over it.

---

## Known Failure Modes

| Failure | Likelihood | Response |
|---|---|---|
| Write failure never triggers a kill switch (documented contract, zero enforcing callers) | **Confirmed present, not yet triggered into a known incident** | Manual vigilance per Mitigation A until fixed; candidate governance gap |
| No integrity-check tooling exists despite being FM-07's canonical mitigation | **Confirmed present** | Manual JSON-validity script (Diagnostics) is the current substitute; candidate governance gap |
| `copytruncate` race can silently drop or corrupt a line written at the exact rotation moment | LOW probability per-day, but structurally always present | Mitigation B |
| `spread_observations.jsonl` / `t4_position_trajectories.jsonl` bypass `AuditLogger` entirely (raw `open()`) — no redaction, no lock | LOW risk today (these are numeric trajectory logs, not obviously secret-bearing) but worth confirming nothing sensitive is ever routed there | Audit the payloads written to these two files if their write sites ever change |
| 30-day local logrotate retention vs. 2-year (ENV-01/02) / 5-year (ENV-03) compliance retention mandate in `DATA_RETENTION_DELETION.md` CAT-04 | Needs confirmation, not verified in this pass | Confirm where/whether a longer-term archive of rotated+compressed logs actually exists before assuming the 30-day local window satisfies the retention policy |

---

## References

- `02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md` — FM-07
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-092 (this runbook)
- `src/prediction_market_bot/c6_audit_logger/audit_logger.py` — full implementation
- `src/prediction_market_bot/c7_monitoring/monitor.py` — real kill-switch mechanism (`is_kill_switch_active`, `KILL_SWITCH_SLA_MS`), currently unwired to C6 write failures
- `deploy/setup.sh:55-74` — logrotate configuration (`copytruncate`, `rotate 30`)
- `08_MODEL_RISK_GOVERNANCE/DATA_RETENTION_DELETION.md` — CAT-04 retention requirements
