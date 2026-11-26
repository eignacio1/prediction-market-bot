# Session handoff — W129.4 PAM holds state (PR #593)

<!-- session-meta
task_id: W129.4
tier: STANDARD
timestamp: 2026-11-26T00:33:00Z
commit: ef45880
one_line_summary: W129.4 merged (PR #593): PAM state tables + NBA backfill 365,975 rows per table; PAM-4 pre-registered, not run.
gg_touched: GG-2005, GG-2003
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NBA PAM classes 1/2/4, D3
gap_delta: D5(b) NBA PAM classes 1/2/4 absent -> aggregated, point-in-time; D3 +1 (H-DEPTH-PAM-4) (MANIFEST.json @ ef45880)
pattern_sweep: n/a (no defect fixed); new code only, naive-timestamp and own-row-in-prior patterns tested in tests/test_pam_state*.py
surface_delta: 0
-->

**Strategic decisions this session**

| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| PAM-4 judged on 2026-27 games after freeze only | 2023-26 were read by earlier tests; only 2026-27 is never-judged | PREREG_PAM4.md | window |


COMMON_RULES_W129 first line (read from origin/main): `# Wave 129 common rules`

## Built
- A: `pam/state.py` — PlayerState, AvailabilityProfile, TraitReliability; append-only JSONL StateStore; ONE read path `as_of(..., known_at=)`.
  Rows carry as_of_ts, known_at, source, version. 7 look-ahead tests (late-known row hidden, future row hidden, trade changes team from its date).
- B: `pam/nba_state_backfill.py` + `scripts/pam_state_backfill_nba.py`; streamed gz, run in session (587s). Rows git-ignored (`exp_output/PAM_STATE/`);
  `12_EXPLORATORY/pam_state/MANIFEST.json` holds counts + sha256.
  - player_state 365,975 rows; availability_profile 365,975 rows (2016..2026, 11 seasons); trait_reliability 8 rows.
- C: `12_EXPLORATORY/pam_state/PREREG_PAM4.md` (H-DEPTH-PAM-4, role security). NOT RUN. HYPOTHESIS_DOCTRINE row added. §6 dated note in PAM_ATTRIBUTE_CLASSES.md.

## Spot-check (30 rows vs box scores, hand loop, seasons 2018/2024/2026)
28 of 30 match usage_rate_shrunk to 5 decimals. 2 differ (0.003, 0.0001): both players played the NBA Cup final (nba-cup, ids 006…),
which the backfill excludes by design (KEEP_TYPES = regular-season, playoffs, play-in).

## Nulls (named, by design)
role_security, return_window (class 4 = PAM-4 hypothesis); missed_by_body_part, recurrence_flags, expected_games_dist (cached reports have no body part);
trait r interval; teammates_out and vacated_usage_share before 2022-23 and on days with no report (null = unknown, never 0).
Out-name match to box names ~71%, so teammates_out is a lower bound.

## Named choices
usage k = 60.1 pseudo-minutes (PAM-3's points k, stand-in); minutes_expected is an unfitted baseline + proportional redistribution, capped 42, unscored;
trait_reliability known_at = 2022-07-01 (valid for decisions judged 2023+); decision time = tip_earliest − 4h; imputed-tip games skipped.

## Measure moved
D5(b) NBA PAM classes 1, 2, 4: absent → aggregated, point-in-time (class 4 is the nulls above plus the pre-reg). D3 +1 pre-registered test (H-DEPTH-PAM-4).
GG-2005: state tables and backfill delivered; role_security/return_window/body-part fields remain open. GG-2003: see PR.

## Not done
PAM-4 not run. No fitted minutes model. No body-part parse. surface_delta: 0 runtime components (library + one hand-run script).
pattern_sweep: grepped src/ scripts/ tests/ for naive-timestamp parsing and exclusive-cumsum priors; the new code is the only user of the state tables.
directive_conflicts: none. operator decisions: none needed; CLAUDE.md RIGHT NOW is RED (window lines 8 days old) — strategic window owns it.
ROLLING_BACKLOG.json not edited. precheck_changed: 112 passed, 1 flaky dashboard test (passes alone).
