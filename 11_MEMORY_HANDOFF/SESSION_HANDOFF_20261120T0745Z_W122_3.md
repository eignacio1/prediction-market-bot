<!-- session-meta
task_id: W122.3
tier: STANDARD
timestamp: 2026-11-20T17:45:00Z
commit: 6daac0d
one_line_summary: W122.3: NFL PASS_YDS T1 priced at its own horizon (pre24h slot + d6_read); 16 in-play cells need a live feed; Part C awaits 11-22/23 slate
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D6 NFL, NFL layer-1 cells (12 -> N)
gap_delta: none yet (12 -> 12 today; 13 expected after the 11-22/23 slate, source d6_read)
pattern_sweep: n/a (no defect fixed; corrected my own first read of PASS_YDS T1 in this handoff)
surface_delta: +1 slot on an existing cron (passyds_prekickoff_snapshot pre24h); no new cron line, service or workflow
-->

# Handoff W122.3 - NFL layer 1: PASS_YDS T1 wired (option 2, operator "Proceed with recommended" 2026-11-20)

Rules read: origin/main COMMON_RULES_W122.md ("# Wave 122 common rules"). Branch w122-3-passyds-t1 (PR). Kelly untouched.

## Part A.1 - the 17 NFL cells without a model p (29 NFL cells; 12 priced = 4 families x T1-T3)
- 8: four families x T4 / T5. Cause: in-play; board_v2 is a pre-game library + tilt, no score / clock / possession input.
- 8: four families x T4NFL-ARITH / FLOW. Same cause, bands also BLOCKED (requires_realtime). No NFL live feed in c1 (NBA only).
- 1: NFL_PLAYER_PASS_YDS T1. Cause (found on reading, corrects my first read): the frozen model passyds_strike_v1 ALREADY prices
  (model_fields in the snapshot job) but only in the pre30 / pre2h slots (0-2 h before kickoff), which are not the T1 band
  (12-48 h), and d6_read only reads PREGAME_SHADOW ledger rows, never the passyds snap store.

## Built (code, PR)
- scripts/passyds_prekickoff_snapshot.py: new slot pre24h (23-25 h before kickoff, inside T1); cron cadence unchanged (20 min).
  Adds ~1 book fetch per strike per game; per-run / daily / store caps unchanged.
- scripts/d6_read.py: passyds_t1_rows credits NFL_PLAYER_PASS_YDS x T1 layer 1 ONLY from pre24h rows with a non-null model_p.
  pre30 / pre2h rows are never credited to T1.
- tests: slot windows, band check, reader (tests/test_w122_3_passyds_t1.py). 50 passed locally with silent_arms / d6 tests.

## Not done / for the window
- Part C not run: needs the 11-22 / 23 slate (no future data). After a Sunday with pre24h rows on the box, run d6_read;
  expected NFL layer 1 12 -> 13 only if rows carry model_p (cold-start / QB-out rows are null by design).
- PASS_YDS T1 stays NOT_IMPLEMENTED in the registry (shadow promotion is a registry change, not made). D6 NFL stays 0: the cell
  still lacks layers 2-7.
- 16 in-play NFL cells: need an NFL live-state feed + remaining-game pricer, its own block.
- Deploy: the box deploys itself on a timer; check deploy_truth_read after merge. surface_delta: +1 slot on an existing cron.

MEASURE MOVED: none yet (NFL layer-1 cells 12 -> 12 today; 13 expected after the 11-22 / 23 slate). directive_conflicts: none checked.

## Strategic Decisions This Session
| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| Re-scope 122.3 to PASS_YDS T1; queue live-feed block separately | 16 of 17 cells need live state | DECISION_LOG 2026-11-20 W122.3 | Operator ("Proceed with recommended") |

One thing pending: after the 11-22/23 slate, run `scripts/d6_read.py` (Part C). Shipped: PR #542 (code), #546 (docs); box HEAD = origin/main.
Resume: read this file, then `git fetch origin && python3 scripts/d6_read.py`.
