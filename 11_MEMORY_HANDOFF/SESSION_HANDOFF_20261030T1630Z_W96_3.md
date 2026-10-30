# SESSION HANDOFF — W96.3 (20261030T1630Z)

Status: PARTIAL | B-003 (rolling backlog on /visual): DONE, read back on the box. B-004 (demo orders that cannot pay, GG-1481): logging shipped and live, cause NOT proven, no fix needed today. Part C (B-006) not run (not in the pasted block) | branches session/20261030T153152Z-w96-3-backlog-demo-balance and ...-partb -> main | PR #382 (`edda7ff`) and PR #384 (`32ce531`) merged, CI green on the current head each time | backlog panel on the box 0 -> 1; refused-order cause still open.

MEASURE MOVED: PLUMBING + EXECUTION. Backlog on the Visual Dashboard 0 -> 1 (box `dashboard_pages_read` 2026-10-30T16:00:31Z, dashboard NRestarts=0). Refused demo orders n -> 0 is NOT claimed as a fix: shadow refusals stopped by themselves after 2026-10-29T00:16Z (zero in ~39 h with orders still placing); the cause is unproven. What moved is the missing instrument: refusals now carry the balance and open exposure.

Stage per factor: none (no factor built).

Part B facts (details and per-day table in `12_EXPLORATORY/demo_balance_w96/results_W96_3.md`): shadow refusals first 10-12T23:13Z, worst 10-15 (1,455), none on 10-18/20/21/26/30; paper T4 had 2,000 rejections on 10-26..28 and no orders since 10-29. Balance over time does not exist before this block. Cause hypothesis (cash reserved by resting shadow orders on the shared demo account at evening peaks) unverified. The only code remedy (guard reserves in-flight exposure) changes order gating, which was out of scope.

Deploy: box HEAD `f6fb0463`; t4-mlb restarted 16:06:31Z by the deploy policy (`demo_fill_policy.py` and `paper_trader.py` changed, no game in progress). Dashboard cold-start after that restart timed out twice on /api/data and /visual at 60 s with memory 123.6 MB of 134 MB; re-read at 16:27Z was healthy (200 in 0.88 s, NRestarts=0). One observation, not registered.

Operator decisions: none. If refusals return, the operator step is a top-up of the Kalshi demo account by login (plumbing); not needed today.

Next: after the first evening game window with a refused order, read `kalshi_order_failed` rows for `demo_balance_usd` and `open_exposure_usd` and decide the cause; then GG-1481 can close or fix. Not done: Part C B-006.

```
task_id: T-1510
vision_pillar: PLUMBING
gap_measure: E1 (instrument only; no fill count moved) and dashboard backlog panel
gap_delta: backlog on /visual 0 -> 1; refused-order balance logging 0 -> live (no refusal row since restart yet)
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no running component added; dashboard gained a panel, t4-mlb logging fields added)
```
