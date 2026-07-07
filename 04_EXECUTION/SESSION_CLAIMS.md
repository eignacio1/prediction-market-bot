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
