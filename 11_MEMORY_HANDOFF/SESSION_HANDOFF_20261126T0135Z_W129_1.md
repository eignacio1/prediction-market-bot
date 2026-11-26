# Session handoff W129.1 — NHL depth logging (2026-11-26 ~01:35Z)

<!-- session-meta
task_id: W129.1
tier: STANDARD
timestamp: 2026-11-26T01:35:00Z
commit: 12f7f43
one_line_summary: W129.1: NHL depth filter on in shadow (#589 #597 #599); unknown starters 53/99 -> 0/351; Muse files not on box (no token).
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NHL
gap_delta: NHL unknown-starter share 53/99 -> 0/351 (nhl_depth_recount on box, store prior only, 2026-11-26); confirmed-starter leaves 0
pattern_sweep: grep 'PM_NHL_DEPTH=on' src/ scripts/ tests/ -> 2 stale comments in nhl_depth.py and shadow_route.py fixed in #599; test_w120_2 candidate-set pin updated
surface_delta: 0
-->

## Strategic Decisions This Session
| Decision | Rationale | Ref | Owner |
|---|---|---|---|
| PM_NHL_DEPTH default ON in code (off-switch), not via an *_install task | W120.2 pattern; shadow only, surface GREEN; no cron or service added | #599 | window |

Block: DEPTH D5(b) NHL — goalie / referee / availability splits on every NHL shadow row. Model: Sonnet 5.5.

## Landed
- #589 filter + store-based expected starters (`prior_only` leaf, `expected_starters` field) + `nhl_depth_recount`.
- #597 `env` fix for the `nhl_muse_fetch` box task (systemd-run could not exec `PYTHONPATH=...`).
- #599 `PM_NHL_DEPTH` default ON in shadow (off-switch `PM_NHL_DEPTH=off`, W120.2 pattern), merged 01:20Z as 12f7f43. CI green on the final run.
  Registry row H-DEPTH-NHL-1 updated in the same PR. One older test (W120.2 candidate set) updated to include `nhl_depth`.
- Shadow only: `split_applied` False, orders follow v1, Kelly 0. No PREREG, model hash, v1 leaf map, cron line or kelly_fraction touched.

## Measured (box, store only, days 2026-11-09..11-25)
- 351 games joined; unknown-starter share 0.0 (was 53/99 on 11-10..). All 351 read `prior_only`.
- `prior_only` carries no published-vs-expected signal, so it is not an informative leaf yet.
- Games/day 20.65. The ~370-game judged n is reached on game count about 11-26; games with confirmed-starter leaves exist only where Muse files exist (through 11-24 at the pinned SHA).

## NOT done
- Part A on the box: `nhl_muse_fetch` returns NO_TOKEN (archive private, no token on box). Verified locally only: 30 files (15 goalie, 15 referee, 11-10..11-24, 451,508 bytes), rerun idempotent. Muse data is NOT on the box.
- Post-deploy readback of one slate's rows with `split_leaves` populated: not run. The deploy of #599 was still pending when the window closed. Next window: `deploy_truth_read`, then `nhl_depth_recount` (prints `ROW` lines), and report.
- Session claim and `session_guard.sh` were not run.

operator decisions:
> Muse files on the box: (a) put a read-only GH_TOKEN in the box .env, or (b) approve vendoring the small Muse files. Pin bump past 2026-11-24 is a separate window decision.

## MEASURE MOVED
- D5(b) NHL classes logging on box rows: built → on by default, store-prior leaves only; real-input confirmed starters 0 until Muse files land. Rows with splits: unconfirmed until the readback.
- Unknown-starter share 53/99 → 0/351 (store prior; not informative).
- First judged look: count ~11-26 on games; the informative look waits on the token decision.

## Pushback / Surface / Dependencies
- Pushback: do not read `prior_only` leaves as evidence; the look needs Muse confirmations.
- Surface: surface check GREEN 11-26 00:21Z (budget green, 0 faults, NHL rows written, deploy truth OK). surface_delta: +0 components (flag on an existing candidate arm).
- Dependencies: token or vendoring decision; deploy of #599.
- pattern_sweep: Kalshi two-letter vs store three-letter team codes (alias map in nhl_depth.py).
- No future data used. Data epoch: NO-side fills before 2026-11-06T01:03:42Z are mirror-priced and were not touched.
