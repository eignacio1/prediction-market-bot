# Session handoff — W123.1 · H1 attention: net gap by market family

<!-- session-meta
task_id: W123.1
tier: MICRO
timestamp: 2026-11-20T21:30:00Z
commit: 49be04d
one_line_summary: W123.1: H1 NOT SUPPORTED on 18 judged non-headline families; 18 prop families UNDERPOWERED (no fit window)
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF
gap_measure: P2 (verdicts issued)
gap_delta: P2 +1 (H1, 2026-11-20, 53,262 settled rows joined from PRICE_ARCHIVE to Kalshi public settled results)
pattern_sweep: n/a (new analysis, read-only on archive; no shared contract touched)
surface_delta: 0 (no cron, service or workflow added)
directive_conflicts: none (D-03 / D-05 wording kept: "hypothesis closed (H1, parked for R&D)"; D-28 met: all data existed at paste time)
-->
Common rules first line quoted: "# Wave 123 common rules".

## MEASURE MOVED: PROOF — H1 verdict and held-out net per family
- **Verdict NOT SUPPORTED** under A1 (HYPOTHESIS.md section 8, written before any outcome was joined). 18 non-headline families judged: none has net > 0 with a 90% interval wholly above zero. Highest point estimate MLB period_f7 +0.0031 [-0.0339, +0.0375].
- Pooled held-out net (game-clustered 90%, 2,000 resamples, seed 123): headline -0.0227 [-0.0498, +0.0041] (266 games); non-headline -0.0361 [-0.0442, -0.0276] (257 games).
- Clause 2 (signed): non-headline -0.0423 vs headline -0.0439, a 0.0015 difference; absolute reading: headline larger (0.0613 vs 0.0424).
- BH q 0.10 over 30 judged families keeps one, MLB team_total, negative (-0.0461 [-0.0642, -0.0281]).
- Nine non-headline intervals exclude zero, all negative.
- Full table with markets and games per family: `12_EXPLORATORY/edge_location/h1_attention/RESULT.md`; numbers in `results.json`.

## What is not judged (and why)
- 18 NBA / NFL prop families: props are in the archive only in the last third of each sport's window, so the fit window is empty and A1's direction rule has nothing to fix. UNDERPOWERED, not read. Re-run at 30 held-out games per family (dated addendum).
- NHL goal / assist props (4,533 / 2,552 settled markets): zero snapshots before 15:00Z game date. Outside A1's price rule.
- B2 (Kalshi minus consensus): not testable, NHL 2025-26 consensus has no overlap with the archive; NHL 2026-27 closes not in yet.
- The 24 h-before sensitivity covers NBA / NFL / NHL only (MLB none); agrees with primary, never the verdict.

## Caveats a reader needs
- Price is a fixed 15:00Z snapshot on the game date (no start times in the archive), not the close. Direction is fixed on the fit window, so the held-out net is a one-shot, no-hindsight number.
- "Main line" is the strike nearest 0.5 in each event at that snapshot; alternates are the rest.

## Files
- `12_EXPLORATORY/edge_location/h1_attention/{fetch_settled.py,run_h1.py,results.json,RESULT.md}`; HYPOTHESIS.md Addendum A1; RESEARCH_PROGRAM.md section 7 row; HYPOTHESIS_DOCTRINE.md II.1 H-EDGE-1 row.
- Rerun: `fetch_settled.py <out> <archive>` then `run_h1.py <archive> <out>`. The archive lives in the main checkout, not in a worktree.

## Next
- Lead for routing (not a verdict): raw gaps are positive on alternate totals / team totals (MLB +0.045 / +0.029, NBA +0.043 / +0.032, NHL spread_alt +0.048) but the taker spread plus fee exceeds them. That is H4's maker question.
- ACTIVE_QUEUE NOW row not edited here (shared nav file, Hard Rule 10); strategic window to update.
