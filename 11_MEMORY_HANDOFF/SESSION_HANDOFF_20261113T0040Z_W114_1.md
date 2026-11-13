<!-- session-meta
task_id: W114.1 (B-087)
tier: STANDARD
timestamp: 2026-11-13T00:40:00Z
commit: 499522d
one_line_summary: W114.1: Muse intake (#494) merged; NBA adapter now tags rows with 12 shot-distance filters (#500); 54 leaves scored, 5 kept.
gg_touched: GG-1932
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D-06, D6 layer 3 (NBA)
gap_delta: NBA index entries 24 -> 36; NBA kept splits 27 -> 32 of 239 total; 0 BH survivors
pattern_sweep: nba_adapter is the only NBA filter entry point (grep filter_supply src/ scripts/ tests/); replay script and tests use it unchanged
surface_delta: 0
-->

# Session handoff - W114.1 (B-087), 20261113T0040Z

**Strategic decisions this session:** None - implementation-only (no operator decisions).

**Part A.** PR #494 (Muse intake) merged ae7562b. Docs-only conflicts; kept main's nav files and both DECISION_LOG entries. CI green. Archive never written. Correction: 113.4 DID write a handoff (SESSION_HANDOFF_20261112T2344Z_W113_4.md); its CI-red note is stale.

**Part B.** PR #500 merged 499522d (CI green). `nba_adapter` now adds `distance_filters()` when the prior-season percentile table has all 12 entries (point-in-time unchanged). `build_filter_splits_w112.py` also reads archive_intake leaf scores, same KEPT rule. 54 archive leaves scored, 5 kept, 0 Benjamini-Hochberg survivors: logged and routed, chance-level. Kept splits across sports 27 -> 32 of 239.

**14-day NBA replay (6,572 rows):** RIDE 651 -> 382, NO_BET 5,921 -> 6,190, FADE 0. Kept splits that disagree cancel (split_conflict, 1,394 rows). NFL/NHL unchanged.

**Tables graded (pin cc7bf85):** 4 VERIFIED, 3 MISMATCH (NBA home/road neutral-site, NBA turnovers, NHL penaltiesFor), 7 UNCHECKABLE rows. NBA index entries 24 -> 36.

**Pending:** window confirms `deploy_truth_read` shows 499522d. Also unread: 7 uncheckable rows, archive days after the pin (needs GG-1931 capture + pin refresh).

**Resume:** read ACTIVE_QUEUE.md sitrep, then 114.2 / 114.3 / 114.4 claims. Commits in this session lacked the Co-Authored-By trailer.
