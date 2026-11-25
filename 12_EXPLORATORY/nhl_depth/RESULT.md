# EXP-NHLDEPTH-001 — RESULT (W128.1, 2026-11-24): built, shadow, **not judged**

**Last reviewed:** 2026-11-24. Pre-registration: `PREREG.md` (commit 99f0aa1, before any outcome was joined). No outcome was scored per arm, because no split reached its bar.

## What was joined
99 completed 2026-27 games, 2026-11-10 to 2026-11-23 (NHL free score API; slate dates). Muse goalie snapshots at the pinned SHA, each used only if `snapshot_at_utc` ≤ puck drop − 30 min.

| Split | Leaves in routing words | Games | Verdict |
|---|---|---|---|
| G goalie@game | both_expected 7 · any_backup 39 · unknown 53 | 46 tagged of 99 | **Not judged.** See the data-quality note: the any_backup count is an artefact, not a finding. |
| R officials@game | no leaf scored: crew prior needs ≥1 settled crew-game and shrinks with k=20; fit-half terciles are not yet stable | 0 scored | **Not judged.** Hypothesis stays open; ride (v1) in all leaves. |
| A availability@game | `unknown` on every row: the archive has no point-in-time availability family | 0 | **Abstains.** Not built as a tested split; stage unchanged. |

## Why nothing is judged
- **n:** the 99 games give about 50 held-out games across all leaves. `games_needed` for a 3¢ net effect is 1,030 games (2,318 for 2¢). The minimum detectable effect at 100 games is 9.6¢. No leaf meets MIN_N = 30 per arm in a held-out half (any_backup has 39 games in total, before the fit/held-out split).
- **Data-quality note (G):** the prereg defines "expected" as the team's most-played goalie in its last 10 starts. The loader derives that from earlier *Muse-confirmed* starters only, and Muse confirms few starters (many rows are `Unconfirmed`; two days are fetch-failure markers). With one or two prior confirmed starts per team, any change of goalie reads as `confirmed_backup`, so 39 of 46 tagged games landing in any_backup is the sparse-history artefact. The fix is to take prior starters from the NHL event store boxscores (the box, not the Muse window), which changes the input, not the leaf definition. Until that is done the G leaf must not be read.
- Marker rows (fetch failure, NO_GAMES) are skipped, never imputed.

## Routing consequence
None. No split earns a leaf in any tree; every leaf keeps its v1 / router v2 arm (ride). Next look: when the held-out half reaches ~370 games for a 5¢ effect (late January at ~6 games a night), with prior starters taken from the box store.

## Stage changes (SEATS/nhl.toml)
None. No split reached a tested verdict, so H9 (officials), H10, H11 and H12 stay at `none`. The splits are *built, shadow-only, unjudged* behind `PM_NHL_DEPTH=on` (default off).
