<!-- session-meta
task_id: W104.3
tier: STANDARD
timestamp: 2026-11-06T02:04:00Z
commit: PRs #436 dd10a8a, #434 c15b980, #433 4dc01cf, #438 e37ff29 + docs-only results push
one_line_summary: W104.3 landed all three stranded Wave 103 PRs green, closed GG-1783 by PR, and closed GG-1775 (a scoring defect, not selection) with a rescore; post-epoch half has n=0.
gg_touched: GG-1775 (resolved), GG-1783 (resolved), GG-1810 (registered)
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION/PLUMBING
gap_measure: E3 (win rate on fills vs non-fills) readability; Wave 103 PRs merged
gap_delta: Wave 103 PRs merged 0 of 3 -> 3 of 3; GG-1775 and GG-1783 closed; GG-1810 registered. E3 itself not re-computed (post-epoch n = 0).
pattern_sweep: GG-1783 side-flip: swept scripts/ for raw order side reads. Fixed demo_fill_timing_audit_collect.py and demo_fill_timing_audit.py, moved the rule into one helper (effective_side) used by order_price_side. scripts/w102_3_night/collect_night.py:31 copies a log field, not an order GET - left. Stale cache entries: GG-1810.
surface_delta: 0 (no cron, service or workflow)
-->

# SESSION HANDOFF - W104.3 (URGENT: land Wave 103's stranded work; GG-1775; GG-1783)
Common rules first line (quoted from origin/main): `# Wave 104 common rules`.

**Status: DONE** | backlog ticket: none (urgent landing block) | PRs and CI: below | **MEASURE MOVED:** Wave 103 PRs merged 3 of 3 (was 0 of 3); GG-1775 and GG-1783 closed; GG-1810 registered | stage per factor: none touched (plumbing and measurement) | operator decisions: none.

## Part A - landed, in order, each merged only on a green CI run of its current head
| PR | head tested | merge | note |
|---|---|---|---|
| #436 CI trim + `scripts/precheck_changed.py` | 4a56676 | dd10a8a | red before only because main was red; ROLLING_BACKLOG.md taken from main (generated) |
| #434 103.2 price dynamics | a4cd434 | c15b980 | DECISION_LOG conflict: both entries kept |
| #433 103.3 in-play NBA/NHL | 234d94d | 4dc01cf | nav files taken from main; DECISION_LOG both kept |
Conflicts changed no logic. No force-push. Main's fence and isolation tests pass after the merges (194 selected tests passed); the `recompute.py:35` fence failure #434's handoff described does not reproduce on main.

**The block's premise was wrong on one point:** `SESSION_HANDOFF_20261106T0300Z_W103_2.md` and `..._0101Z_W103_3.md` already existed inside their PRs, with session-meta. I verified them against the PRs' files and did not rewrite them. Two corrections for the reader, written by 104.3: (1) the W103_3 handoff says "PR #433 NOT merged, CI NOT confirmed green" - that was true then; #433 merged at 4dc01cf on green. (2) the W103_2 handoff is stamped 03:00Z, ahead of the real time it was written (~01:5xZ).
What they say, for the record: 103.2 - 22 of 22 series have a 60-minute give-back estimate (game-clustered bootstrap, seed 20261105, Holm 0.05 / BH 0.10); Holm-significant fades KXMLBHIT (largely bid-ask bounce), KXNFLTEAMTOTAL (+0.29), KXNHLTOTAL (+0.51); BH-only KXMLBF5SPREAD, KXNHLTEAMTOTAL; no significant follows; stage aggregated + interpreted, not applied. 103.3 - NBA diffusion (n=1229 held-out games, Brier 0.191/0.156/0.120 at Q1/Q2/Q3 end vs 0.205 pre-game) and NHL Poisson jump process (n=1312); vs-market n=0 for both; stage interpreted, not applied.
**Box deploy:** `logs/vps_deploy.log` shows the box deploying through #438 (HEAD e37ff29f, rc=0). t4-mlb restart decision: **not_needed** - no file t4-mlb imports changed; only pmbot-web-dashboard restarted. t4-mlb is active.

## Part B - GG-1775: CLOSED (cause found), post-epoch half waiting on data
Full table and method: `12_EXPLORATORY/w104_landing/GG1775_REMEASURE.md`. Cause is scoring: the forward cache stored every NO buy as `side=yes` and scored it backwards (17,312 of 38,719 filled entries are intended-NO). Rescored by intended side, pre-epoch fills win BELOW price in every sport (YES-only NHL -0.015, NFL -0.047, NBA -0.073, MLB -0.082). **Post-epoch fills: n = 0** (cache stops 2026-11-05 11:43Z, before the epoch), so "is the gap gone after the fix" is answered for the mechanism, not yet for fresh data. ADR-0072 verdicts unaffected (#435 epoch floor). Remainder: GG-1810 (stale cache entries), and `quant_w103_tails` shadow tails need recomputing on rescored fills (for the window).

## Part C - GG-1783: CLOSED by PR #438 (head tested green; merge e37ff29)
Collector records `action`, the side actually bought, `side_normalized`; reader normalizes legacy rows and prints a warning for rows lacking `action`. 3 new tests in `tests/test_demo_fill_forward_report.py` (flip rule, legacy normalization incl. idempotence, `order_price_side` regression); 39 pass.

## Not done / for the window
- Session-start protocol Steps 1-4 / Q-checks were not re-run in this resumed block beyond the claim and worktree; no concern raised from them.
- Post-epoch GG-1775 re-measure: rerun once the forward report has post-epoch fills (a read of the same cache; the method is in the RESULT file).
- Recompute the shadow tail numbers in `quant_w103_tails/RESULT.md` from rescored fills.
