# W83.2 results (Part A capture, Part B play-type grade and absorber cross)

**Date:** 2026-10-21 · **Pillar/measure:** DEPTH D5(b) NBA · **Decisions logged:** false (DECISION_LOG row at session end)
**Archive pin:** eignacio1/sports-intel-archive @ `e2000aa78e43cb6380382ac1f7537d7f3443e76e` (descendant of 2ce6b77), read-only.
**Code:** `playtype_absorption.py` (this folder). Result file: `playtype_absorption_result.json`. 2025-26 regular season, 1,230 games.

## Part A: lineup window
Capture job `scripts/nba_lineup_window_capture.py`, cron `3,18,33,48 * * * *` (3 minutes after each 15-minute report slot; the PDFs
land on a 15-minute grid with Last-Modified to the second, so 15 minutes is the finest cadence the source has). Pre-registration
frozen in `PREREG_lineup_window.md` before the first row; modal outcome stated there (REAL-AND-PRICED ~50%). Install and read-back
status is in `results_partA.md` and the handoff.

## Part B, step 1: grading Muse's play-type class (charter section 5)
**What the event store cannot do:** pbp carries shot sub-types (pull-up, driving, cutting, hook, dunk), assists and possession
starts, but no screen, handoff or isolation labels. NBA.com publishes no definition of the Synergy categories either. So Muse's
frequencies (share of a player's possessions in each play type) are **not gradeable as numbers**. What can be graded is the
**ordering** across players, through one proxy per class fixed in the script before the run:

| Muse class | Event-store proxy | n players | Spearman | top-15 overlap | Reading |
|---|---|---|---|---|---|
| Isolation | share of FGA that are pull-up/step-back/driving/fadeaway/turnaround | 296 | 0.60 | 5 | ordering holds |
| P&R ball handler | assists per minute | 334 | 0.64 | 8 | ordering holds |
| Spot-up | assisted share of made 3s | 349 | 0.45 | 1 | weak |
| Transition | share of FGA within 8s of possession start | 422 | 0.34 | 3 | weak |
| Cut | cutting-shot share of FGA | 380 | 0.79 | 9 | ordering holds |
| Post-up | hook-shot share of FGA | 169 | 0.41 | 5 | weak |
| P&R roll man | dunk share of FGA | 317 | 0.56 | 4 | ordering holds |

Qualifier: 10+ minutes per game and 50+ FGA (3-pt classes: 20+ made 3s); Muse's own rows already carry the site's 10-possession
cut. The 0.5 line for "holds" was my reading rule, set while writing this table, after the run, so it is a reading and not a
pre-registered threshold.

**Grade: PARTIAL, no class FAILED.** Frequencies not gradeable (no labels). Ordering consistent with the event store on 4 of 7
classes (Cut strongest, Spot-up/Transition/Post-up weakest). The weak classes are the ones where the proxy is the poorer
stand-in (a transition shot is not only a fast shot; a spot-up three is not only an assisted three), so a low correlation there
says as much about the proxy as about Muse. This does not VERIFY the numbers; it says the class is not contradicted.

## Part B, step 2: absorber play-type profile x usage absorption (2025-26, interpreted only)
Creators: each team's top-2 by usage events per game (FGA + 0.44 FTA + TOV) with 15+ games played, who missed 3+ games to
injury, rest, suspension or not-with-team (coach's decisions excluded) and played 10+ games. Absorber: a teammate with 10+ games
with and 3+ without. Absorption = (absorber's events per game without minus with) / creator's events per game.

- **n = 131 absorber-creator pairs, 13 creators, 10 teams.** Mean absorption per teammate 0.10 of the creator's usage.
- **Split-half reliability** of a pair's absorption (odd vs even absence games): r = 0.38. The measurement is noisy.
- **Profile effect** (cluster bootstrap by creator, 2,000 draws): composite profile (self-creation + assists per minute minus
  assisted-3 share) Spearman **+0.06, 95% CI [-0.11, +0.24]**; self-creation +0.07 [-0.10, +0.24]; assists per minute +0.09
  [-0.09, +0.26]; assisted-3 share -0.10 [-0.27, +0.06]. Halves: +0.02 and +0.13.

**Reading:** the direction is the expected one (creators absorb creation, spot-up shooters absorb less) but no interval excludes
zero, and 13 creators is a small cluster count. **Stage: interpreted, with a null at this n.** It does not support a profile
adjustment to the +1.75 / +1.00 / +0.34 role shifts; more absence games (the live capture, and 2026-27) are what could move it.
No price test was run.

## Stage per factor (ADR-0075)
- NBA-10 lineup cross: interpreted -> **testable** (live timestamped capture running, pre-registration frozen). Not applied.
- NBA-11 absorber profile x absorption: **interpreted** (null at n=13 creators).
- NBA-7 play-type: still none (no labels in the store); Muse's table is a one-off snapshot and its ordering is partly corroborated.
