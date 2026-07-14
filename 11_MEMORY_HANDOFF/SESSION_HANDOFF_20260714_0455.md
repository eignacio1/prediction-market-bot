# Session Handoff — 2026-07-14T04:55Z

**Trigger:** Operator-initiated (`/session-end`), clean cutover — task (C8 dashboard fix) already complete and verified before this protocol ran.
**Last commit:** `63eed9b` (main, merged) — pushed to GitHub + VPS. This session's own governance/doc commit (GG-118/T-356/DECISION_LOG/MEMORY_BANK/PLAN/TODO_NEXT/SESSION_CLAIMS) is being committed immediately after this file, path-scoped.

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** Not re-run this session (doc/governance + one code fix in a stdlib-only, non-pytest-covered script; last known full-suite baseline: 2685 passed / 29 skipped, per most recent prior session's confirmation — not independently re-verified here)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; `pmbot-web-dashboard.service` restarted post-fix, confirmed stable (`MemoryCurrent`~20MB vs 128MB cap, `NRestarts=0`)
- **Paper bets:** G6 gate unchanged this session (no capital-affecting action taken) — see MEMORY_BANK.md Current State Snapshot for the live per-band `clean_n`/G6 figures; this session did not re-pull the ledger

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Fixed the `pmbot-web-dashboard` OOM-kill loop via a bounded `deque(maxlen=tail)` read in `_load_jsonl()` rather than raising the systemd `MemoryMax=128M` cap. | Raising the cap would mask the underlying unbounded-parsing bug and only buy headroom until logs grew again — the defect scaled with file size, not the `tail` bound it was supposed to respect. The code fix removes the scaling defect at its source. | DECISION_LOG.md 2026-07-13 (row 1) | Claude |
| Resolved a `git push` rejection by using `git merge origin/main` instead of `git pull --rebase`. | A concurrent session had uncommitted, non-overlapping, security-sensitive changes (an API-key redaction, GG-116) in the shared tree; rebase requires a clean tree and would have forced an unsafe stash of that work (Hard Rule 10/GG-101). Merge does not require a clean tree when the incoming commit touches an unrelated file. | DECISION_LOG.md 2026-07-13 (row 2) | Claude |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| C8 dashboard OOM-kill fix (GG-118) | ✅ Root-caused (`_load_jsonl()` unbounded-memory parse vs. 128MB systemd cap), fixed (`scripts/web_dashboard.py`, bounded `deque`), verified (synthetic 200k-line test + live VPS memory/restart-count check + end-to-end SSH-tunnel path), deployed, committed (`f6d7a85`), merged to `main` (`63eed9b`). |
| Governance documentation for GG-118 | ✅ `GOVERNANCE_GAP_LOG.md` GG-118 entry (RESOLVED code fix / OPEN detection gap), `DECISION_LOG.md` two Notable Judgment Calls rows, `TODO_NEXT.md` T-356 registered + "Last reviewed" header, `MEMORY_BANK.md`/`PLAN.md` "Last reviewed" headers updated, `SESSION_CLAIMS.md` claim row added (checked live for collisions before minting GG-118/T-356 — none found). |

---

## ONE THING PENDING

**T-356 is OPEN, not yet implemented:** add a `pmbot-web-dashboard` health probe (recent `oom-kill` count via `journalctl`, or `NRestarts` via `systemctl show`) to CLAUDE.md's Step 4 operational health check. Step 4 currently has zero coverage for this service — `systemctl is-active` alone will not catch a restart loop, since the service re-enters `active` within ~5s of each crash. This is a doc-only change (one new command in CLAUDE.md's Step 4 block) — no code to write, no data to pull. Full detail and a proposed command in TODO_NEXT.md's T-356 section.

---

## Current Paper Portfolio

*Not re-pulled this session (no capital-affecting action taken). Freshest available reads, per MEMORY_BANK.md's 2026-07-11 consolidated snapshot:*
- MLB T1/T2 (ACTIVE): bankroll $877.85, 22 open ($205.82 deployed), 216 resolved, P&L +$83.68
- MLB T4M-PROJ (ACTIVE): bankroll $1,000.00, 69 open ($38.48 deployed), 515 resolved, P&L +$32.35
- NBA (DARK/FROZEN, standing operator directive): $751.10, 0 open, 158 resolved, 24.9% drawdown, −$248.90
- G6 gate: unchanged this session — see MEMORY_BANK.md for the live per-band `clean_n` vs. `n*` standard (APR-0024)

---

## Active Cron on VPS (157.230.91.33)

Unchanged this session. See CLAUDE.md Step 4 for the current health-check commands (T1 MLB cron, T4 MLB systemd, T1 NBA cron, semantic-oracle counters). `pmbot-web-dashboard.service` is systemd-managed, not cron; restarted this session as part of the GG-118 fix.

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (per-band `clean_n ≥ n*`, APR-0024, superseding the flat 30/150/500 heuristic for go-forward language — GG-004's n=151 DIRECTIONAL_POSITIVE verdict itself stands unretracted)
3. `pmbot-web-dashboard.service`'s `MemoryMax=128M` cap is now safe again post-fix, but has no session-start monitoring coverage (T-356, OPEN) — if the dashboard goes dark again before T-356 lands, check `journalctl -u pmbot-web-dashboard.service | grep oom-kill` first.

---

## ⚙️ DECISION AUDIT

Not applicable — no strategic/architecture document (`02_ARCHITECTURE_DESIGN/`, `08_MODEL_RISK_GOVERNANCE/`, `01_SPEC/`) was created or modified this session. Step 0 governance scan re-run at session-end: no `decisions_logged: false` matches introduced by this session's changes (only `GOVERNANCE_GAP_LOG.md`, `DECISION_LOG.md`, `TODO_NEXT.md`, `MEMORY_BANK.md`, `PLAN.md`, `SESSION_CLAIMS.md`, `scripts/web_dashboard.py` were touched — none carry a `decisions_logged` field).

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260714_0455.md, then pick up T-356 (CLAUDE.md Step 4 health-probe gap for pmbot-web-dashboard)."
```
