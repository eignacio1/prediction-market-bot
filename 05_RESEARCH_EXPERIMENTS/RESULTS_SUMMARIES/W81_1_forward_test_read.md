# W81.1 — The forward test, read (PARTIAL: Part A code merged, box table pending; Part B descriptive only; Part C not started)

Date: 2026-10-20T05:40Z. Source: PR #297 (merged, CI `test` pass), `logs/demo_fill_policy.jsonl` copy (46,435 lines), box HEAD 9d69a6bf.

## What was done
- Report now labels (book, sport, arm). Arm = recorded arm at/after 2026-10-13T23:58Z (cancel-path fix epoch); `control_arm` skips -> control; shadow cancel events inherit the order's arm; everything else (no-arm shadow orders, paper rows, other skips, pre-epoch) -> `unassigned_pre_test`. Adds distinct games, fills/game max+median, pre/post top-up (2026-10-16T05:40Z) splits, and an assignment check.
- Assignment check (full log): all 18,795 armed shadow orders match sha256("w64-2|"+row_id) at share 0.5. 0 mismatches. control 9,408 / treatment 9,387.
- Scoreboard: P3 regex, D1 exact-name rules, D4 NBA data_layer fixed with tests (broken inputs 3 -> 0 locally; P3 locally UNAVAILABLE because engine_*.json is VPS-only — not read back on box).
- Log facts: 20,572 shadow orders, 1,777 with no arm (from 2026-10-11T16:38, pre-epoch). Paper control orders are NOT in the log; paper treatment visible only via cancel_scheduled, so paper treatment-vs-control cannot be formed.

## Labelled per-cell table
NOT WRITTEN. The box run (`demo_fill_forward_report.py --out exp_output/FORWARD_TEST/w81_1/...json --no-act`) fetches every order's fill from the demo API and was still running (>20 min, no output file) when the session was closed. Re-run via bridge task `forward_report_read`.

## Verdict (Part B)
Not scored: judged n (~550 clean settled fills per arm) is not reached (ADR-0072; treatment cells ~12-23 fills/cell per W76.1). Verdict: **no verdict yet**, as pre-registered. Descriptive only.
- (a) clustered lower bound: not computed. (b) fill-rate ratio: not computed. (c) 30-min markout: NOT_EVALUABLE (no candle collection).
- Side-by-side readings (per-(book,sport) vs pooled): not computed, since the table is pending.

## Ambiguity for operator (one line)
Pre-reg does not say per-(book,sport) vs pooled, how cash-starved days count, or the fill-rate denominator; recommend per-(book,sport).

## NOT checked
Box labelled table; distance_read bridge read-back (D1/D4/P3 on box); deploy_truth_read; Part C entirely.
