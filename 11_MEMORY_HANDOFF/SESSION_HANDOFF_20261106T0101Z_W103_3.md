<!-- session-meta
task_id: W103.3
tier: STANDARD
timestamp: 2026-11-06T01:01:33Z
commit: PR #433 (code) + docs-only results push
one_line_summary: W103.3 quant lane - NBA diffusion and NHL Poisson jump-process in-play models built with known-answer tests and held out on 2025-26; vs-market comparison not possible (n=0).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF/DEPTH
gap_measure: in-play models built and held-out-tested; vs-market comparison n per sport
gap_delta: in-play models 0 -> 2 (NBA n=1229 games, NHL n=1312 games); vs-market n: NBA 0, NHL 0 (Part C stopped)
pattern_sweep: EV-baseline lesson (a state multiplier fitted against the overall rate must not be re-applied when the pre-game rate already averages the state mix) checked in inplay_nhl.py, nhl_heldout.py and tests; one instance, fixed in the run script (EV multiplier fixed at 1.0)
surface_delta: 0 (library modules and exploratory scripts only; no cron, service or workflow)
-->

# SESSION HANDOFF - W103.3 (quant lane, B-046)
Common rules first line: "# Wave 103 common rules". Results: `12_EXPLORATORY/quant_w103_inplay/RESULT.md`. Code: PR #433 (CI was still pending when this was written; not claimed merged).

**Measure moved:** in-play models built and held-out-tested 0 -> 2. Stage (ADR-0075): interpreted, priced; not applied, because no comparison against the market was possible.

**A. NBA** (`quant/inplay_nba.py`, 10 tests): drifting random walk. Held-out 2025-26, n=1229: Brier 0.191 / 0.156 / 0.120 at Q1 / Q2 / Q3 end versus 0.205 pre-game only. Slightly over-confident at the extremes; OT edge not modelled.

**B. NHL** (`quant/inplay_nhl.py`, 9 tests): Poisson goals with power-play and empty-net states, exact regulation vs OT/SO settlement. Held-out 2025-26 regular season, n=1312: game-win Brier 0.214 / 0.147 / 0.119 / 0.101 versus 0.250. It under-prices regulation ties (0.17-0.19 vs 0.248) and totals (about 0.52 vs 0.573). Score effects are not modelled (training data shows them small). First run applied the even-strength multiplier twice and under-priced goals; fixed as a model-definition correction before reading any result, and disclosed in RESULT.md.

**C. Against the market: not scored, n=0 each.** The archive has in-play snapshots from 2026-10-28, but there is no 2026-27 NBA event store, and the NHL store has game-clock time only, so the score at a snapshot cannot be recovered at 20-minute cadence. Stopped as the block instructs.

**Caveat on every number:** no historical pre-game lines exist, so a walk-forward team rating stands in for the line.

**Not done / honest gaps:** the brief session-start protocol (Steps 1-4, Q-checks) was not run in this block. PR CI green not yet confirmed.

**Recommendation to the window (operator decides nothing):** to unblock Part C, log wall-clock-stamped in-play scores (NBA and NHL) alongside the archive snapshots; then the comparison is one script.

## Close-out addendum (session-end)
- Isolation test (`tests/test_exploratory_isolation.py`) failed CI on efbb782; fixed in 398b8de (held-out scripts write via `_fence.safe_out`). Local: isolation 150 passed, quant 19 passed.
- **PR #433 NOT merged, CI NOT confirmed green:** no workflow run started for head 398b8de (or the empty retrigger commit) after ~15 min; other terminals' runs contended. Push path: local `w103-3-results` -> remote `session/20261106T004640Z-w103-3-inplay-math` (force-push was denied; used cherry-pick + fast-forward).
- One-thing-pending: get CI to run on PR #433 head, then merge. Part C (vs-market) remains n=0.
