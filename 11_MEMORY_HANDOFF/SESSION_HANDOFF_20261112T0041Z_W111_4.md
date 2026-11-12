# Session handoff — W111.4 (B-080) granularity index as tree splits, NBA

vision_pillar: DEPTH
gap_measure: D5(b) NBA applied; index entries with all five parts; D1 NBA; directive D-06
gap_delta: D5(b) NBA 10 -> 11 of 17 (B7 lineup / play-type / situation now applied); entries with all five parts 0 -> 18 (team-level, scored per leaf); D1 NBA: no new factor class (denominator unchanged); D-06 PARTIAL -> PARTIAL (NBA built)
directive_conflicts: none
pattern_sweep: n/a (no defect fixed); the exploratory-isolation failure (writes not via safe_out) was fixed in both new scripts, the only 12_EXPLORATORY files this block added
surface_delta: none (no running component)

## What shipped (PR #485, 3d59e57, CI green)
- Machinery: `nba_engine/situation_splits.py` (Situation rows -> value, rank vs history, stability, cross, frequency).
- 24 entries in `12_EXPLORATORY/granularity_index_nba/` (INDEX.md, entries/*.json).
- Router interface for 111.3: `nba_filters(home_profile, away_profile)` in `nba_engine/filters.py` returns {"<entry>@total": leaf, "<entry>@side": leaf}; profiles map entry -> team percentile (0..1) of the prior-season raw metric. Totals leaves high/mid/low; side leaves home_edge/away_edge/neutral; missing -> "unknown". Never returns a price or side. 111.3 owns router.py; not wired by this block.
- Scoring: `score_leaves.py` -> `leaf_scores.json`. 43,056 deduped rows, 112 fit / 48 held-out games, 85 leaves (18 thin, 49 NO_BET, 36 fit-picked arms: 13 MOMENTUM, 11 MODEL_FADE, 8 RIDE, 4 FADE), 25 reportable. BH survivors 0; drafts 0. Fit-picked arms mostly did not hold out (e.g. clutch_offence_ppp MONEYLINE neutral FADE -0.117 [-0.223,-0.011] n=89). In the tree these leaves are routed to NO_BET provisionally. This is a routing result, not a verdict on any cell.
- Seat: nba.toml B7 -> applied; NBA_SEAT.md regenerated.
- GG-1895 (data limits). D-06 row, ACTIVE_QUEUE row, DECISION_LOG updated.

## Not scored
Four props-only entries (no props rows in NBA shadow families) and two lineup-on-floor entries (tonight's lineup unknown) stay at four parts.

## Protocol outputs
Step 2 stub scan: src/prediction_market_bot/quant/inplay_nhl.py:37: # placeholders that the run script overrides with multipliers fitted on training seasons only.
Step 3 open GGs (anchored count, after GG-1895): 254. Uniqueness check: OK.
Steps 0/1/4 and Q1/Q4/Q5/Q7 were not re-run in this block (docs/exploratory work in an isolated worktree, no box access); Step 4 is not run here.

## Q6 worries
- Lineups are quarter-box granular, not exact after mid-quarter subs (GG-1895).
- Team and clutch PPP are noise-dominated at one season, so the cross shrinks to the league mean; 5 of 24 entries are not stable traits.
- Shadow rows are paper rows, not fills (GG-527); the held-out window is 48 games, game-clustered bootstrap.
- Fit-picked arms fail held-out and 0 leaves survive BH, so the application is machinery, not evidence of lift.
- My first "0% null score join" probe was wrong because blank strings are not NaN; ffill fixed it.

## Next
111.3 may consume `nba_filters`; NFL / NHL / MLB entries are not built. Operator decisions: none.
