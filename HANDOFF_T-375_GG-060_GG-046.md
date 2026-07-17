# Parked session handoff — T-375 / GG-060 / GG-046

**Parked early: context limit approaching. Branch pushed, not merged. Resume here.**

Branch: `session/20260716T053315Z-gg060-monitoring-buildout` (pushed to origin, HEAD `6ad60d5`)
Worktree: `PM-worktrees/20260716T053315Z-gg060-monitoring-buildout`
Claim row: `SESSION_CLAIMS.md`, T-375, "GG-060 monitoring buildout (Phase 2/4 + T1/T4/T2 wiring) + GG-046 T4 commercial-gate re-check"

## Session-start protocol: COMPLETE
Steps 0-4 and Q1-Q6 all run this session. No new governance gap registered (findings folded into work below). Q6 concerns on record: GG-046 clean_n=0 optics (see below), MEMORY_BANK.md 29-header hygiene debt (not in scope, already tracked), and — resolved this session — the GG-060 T4-wiring claim.

## KEY FINDING — GG-060 log entry is stale, verified via git blame
The GOVERNANCE_GAP_LOG.md GG-060 entry (last touched in a 2026-07-15 burndown pass) claims wiring into `run_t4_mlb_live.py` "remains OPEN." **This is false.** `git blame` on `run_t4_mlb_live.py` lines 1293-1333 shows `edge_logger` was already constructed and passed into `RiskEngine(...)` in commit `8d2f1dda` (2026-07-02 13:27:33 -0700), commented explicitly "T-213/GG-060 edge-decision classification sink (Phase 2 — T4 parity with T1)." Confirmed live on VPS: `audit_mlb_t4_edge_decisions.jsonl` has 12,620 lines, last written 2026-07-12 22:47. T4 wiring has been real and producing data for two weeks; the 2026-07-15 burndown pass reaffirmed "no change" without re-verifying the sub-item. This is exactly the Hard-Rule-10 stale-narrative failure mode.

T2 (`run_t2_mlb_sameday.py`) genuinely had **no** edge_logger anywhere — confirmed via grep (zero hits) before I touched it. That was the real remaining wiring gap.

## Work DONE this session
1. **T2 wiring (code-complete, committed `6ad60d5`):** Added `edge_logger = AuditLogger(LOG_DIR / "audit_mlb_t2_edge_decisions.jsonl", ...)` in `main()`, wired into both `RiskEngine(...)` construction sites (initial + the per-bet rebuild inside the loop, ~line 341 and ~line 549 pre-edit). Matches T1/T4 pattern exactly.
2. Confirmed VPS state: T1 edge log 456 lines (last Jul 12), T4 edge log 12,620 lines (last Jul 12), T2 edge log **does not exist yet** (expected — this fix isn't deployed).

## Work NOT DONE — pick up here
1. **Test T2 wiring against real run logs (explicit task requirement — not yet satisfied).** Options: (a) deploy to VPS and observe next T2 cron run produce `audit_mlb_t2_edge_decisions.jsonl`, then run `risk.summarize_edge_run()` against it; (b) run T2 locally in a dry-run/test mode against a real recent `pregame_mlb_*.json` + live Kalshi snapshot if feasible offline. Do NOT deploy without running local unit tests first (`pytest` on the T2 test file, if one exists — not yet checked this session).
2. **Correct the stale GG-060 log entry** — update Status field to reflect: T4 wiring was already done (2026-07-02, commit `8d2f1dda`), T2 wiring done this session (pending live verification), Phases 2 and 4 still open.
3. **Phase 2 — 7-day edge-rate trend.** Not started. Likely a small script reading the three edge-decision JSONL sinks (T1/T4/T2) across the last 7 days, computing `edge_signals_found / total_evaluations` rate per day per band, flagging sustained drift. Natural home: alongside `summarize_edge_run()` in `risk.py`, or a new `scripts/edge_rate_trend.py`. Check `dashboard.py` Panel 6 for the rendering pattern already in use (lines ~830-965).
4. **Phase 4 — EXP-017/EXP-T4-01 retrospective template.** Not started. Should consume the edge-decision JSONL sinks to produce the same accounting EXP-017/EXP-T4-01 need (net_edge vs realized outcome), reusable across re-runs so future EXP re-runs don't require bespoke one-off scripts. Check `scripts/run_exp017_mlb.py` for the existing EXP-017 pattern before designing this.
5. **GG-046 re-check — NOT DONE.** Must pull live `clean_n` for T4M-PROJ fresh from VPS (Hard Rule 10 — do not reuse the stale 338 figure from 2026-07-11, or anything cached in this document). **Known context going in:** three epoch bumps landed this week (GG-113 epoch→4 on 07-14, GG-119/ADR-0045 epoch→5, GG-122/APR-0028 epoch→6, all 07-15/16) — since `logic_epoch.py`'s counter is deliberately global (not per-band, confirmed by reading the module docstring this session), **every band's clean_n reset to 0 regardless of which band's write-path each fix actually touched.** T4M-PROJ's clean_n is very likely 0 right now, not because anything about T4M-PROJ broke, but as a side effect of unrelated T1/T2 fixes. **When writing this up: state that context explicitly, don't let a bare "clean_n=0" read as a T4M-PROJ regression.** Since 0 < 500 and 0 < 787, this is the "still short" branch of the task instruction — build the automated threshold-crossing check (task's own suggestion: alongside Step 4 VPS health check, or standalone script). Do NOT re-run EXP-T4-01 without registering that decision separately first (explicit task constraint).
6. **DECISION_LOG.md entries — NOT YET WRITTEN.** Hard Rule 7 requires logging immediately; this got deferred by the context-limit parking. At minimum, log: (a) the GG-060 T4-wiring stale-log finding, (b) the T2 wiring change, (c) the GG-046 clean_n/epoch-cascade finding once confirmed fresh.
7. **Session-end (SESSION_HANDOFF, checkpoint, operator digest) — NOT RUN.** Run `/session-end` once items 1-6 above are complete, or run it now in a degraded/partial form if the next session is also going to be context-constrained — operator's call.

## Do NOT touch (exclusion list, unchanged)
GG-020, GG-044, GG-059, GG-072, GG-091, GG-045, GG-105, anything NBA-tagged. Also observed this session: concurrent claims T-374 ("GG-easy-sweep": GG-044/GG-072/GG-020/GG-059) and a TBD-range claim on GG-105 — both actively worked by other sessions, confirms staying clear is correct, not just cautious.
