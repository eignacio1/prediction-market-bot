# Session Claims Log (GG-082)

**Purpose:** Make concurrent sessions visible to each other *before* they conflate work in a shared navigation file, not after. Append-only — one row per session, added at session start per CLAUDE.md Step 0. Commit and push the row immediately, on its own, before doing any other work.

**How to use this file:**
1. At session start, append a row: UTC timestamp, your intended `T-NNN`/`GG-NNN` range (or "TBD" if not yet known), one-line focus.
2. Commit and push that row by itself.
3. Before writing to `MEMORY_BANK.md`, `PLAN.md`, `DECISION_LOG.md`, `TODO_NEXT.md`, or `GOVERNANCE_GAP_LOG.md`, check this file for any other claim from roughly the last 24 hours — if one exists, diff the target shared file against `HEAD` before trusting its currently-loaded narrative (per Hard Rule 10).
4. Do not edit or delete other sessions' rows. This is a log, not a lock — it does not block work, it makes concurrent activity visible.

| UTC Timestamp | Claimed T-NNN / GG-NNN Range | Session Focus |
|---|---|---|
| 2026-07-06T16:34Z | T-243, GG-027, GG-082 | GG-027 re-scope (PAM-MLB finding), GG-082 process-guard implementation (this file) |
2026-07-06T23:50:52Z | T-NNN/GG-NNN: TBD | Focus: advisory discussion on edge-strategy transition (Opus decomposition recommendation review) — no code changes anticipated
| 2026-07-06T23:54:44Z | GG-054 (done), GG-055 (done), GG-065, GG-074, GG-075 | Continuation of governance-gap sprint: py.typed/mypy strict enforcement (GG-065), stale-doc review process (GG-074), ACCEPTANCE_CRITERIA.md evidence trail (GG-075)
| 2026-07-07T04:03:06Z | GG-092, GG-093, GG-094, GG-095, GG-096 | Triage batch for 5 new gaps from GG-074 closeout, priority GG-095 (Brier drift ladder mismatch near kill switch) |
| 2026-07-07T04:31Z | EXP-017B/C/D, GG-097, T-247/248/249, ADR-0041 | Edge-decomposition of the n=151 T1 MLB book (017B), calibration root-cause (017C), A/B edge-delta harness build+first run (017D). Adds files under exp_output/ + scripts/; section-anchored appends to DECISION_LOG/GG_LOG/TODO_NEXT/MEMORY_BANK. Numbers chosen above all prior claims — reconcile if a concurrent session grabbed GG-097/T-247/ADR-0041. |
| 2026-07-07T05:10Z (GG-095 session, reconciliation note) | T-247 COLLISION FLAGGED | The 2026-07-07T04:03:06Z claim (this same session) completed and fully committed T-247 to DECISION_LOG.md + GOVERNANCE_GAP_LOG.md for GG-095 (monitor.py L3/L4 Brier-ladder fix) before this 04:31Z claim's T-247/248/249/GG-097/ADR-0041 reservation was written to those files. Per this file's own "reconcile if a concurrent session grabbed" instruction: T-247 stays assigned to GG-095 (already merged to origin/main). The EXP-017B/C/D session should renumber its pending DECISION_LOG/GG_LOG/ADR appends to the next free slots (T-250+, GG-098+, ADR-0042+ — re-check highest-in-use at commit time, do not assume these are still free either) when it commits its own docs. |
