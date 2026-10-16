# Qualitative archive → bot: intake contract (DRAFT v0)

**Status:** DRAFT, 2026-10-15 (strategic window). Nothing built. The adapter is a Wave 78 block. **Decisions logged:** DECISION_LOG
2026-10-15 22:09 PT.

**What it is.** The operator is building, with Muse, a "mass data scraper ... to compile as comprehensive of an archive as
possible - it will continue to get deeper and more complex with the layers" (2026-10-15). It is the Sports Intelligence Archive:
`MUSE_ARCHIVE_ARCHITECTURE_20261015.md` beside this file. NFL base is complete (L1 foundational, L2 schematic, team-news,
cross-team: the undervalued board, the trajectory index, league trends). NBA, NHL and MLB are queued, and L3 is undecided.

**Why it matters here.** It is the first source for the factor class nothing in the project had: **G5 qualitative** ("None free
and structured", FACTOR_TAXONOMY.md), the sixth D1 class, which no live model conditions on. It also feeds four ADR-0075
components directly:

| Archive part | Feeds | How |
|---|---|---|
| L1 team files (org, personnel, scheme, coaching, trajectory, insider-obvious) | G5 qualitative factors; seat interface | per-team claims → factors in the seat files, at the aggregated stage until a price path is tested |
| L2 schematic (scheme mechanics, coordinator fingerprints, matchup levers) | factor classes F5/F6 (scheme) and matchup | a qualitative prior next to the play-level tendency the engine measures; the test is whether it adds to it |
| Undervalued board (`undervalued-watch.md`: 128 flags, each with the mechanism) | PAM deep tier (cluster designs) | evidence lines for deep-tier records, never a label by itself (DEEP_TIER.md layer 2) |
| Trajectory index | seat interface (cell routing); temporal evolution | a trajectory shift flags which `(market_type, band)` cells to re-examine |
| League trends | structural priors; structural tensions | league-wide assumptions; a trend the engine cannot represent is a tension |
| team-news sentiment trajectory | momentum looping / timing | sentiment as a when-signal, tested against price paths |
| updates/ (dated deltas) | point-in-time read path | the only safe way to read the archive as of a past date |

## The requirements (what the archive must give, and what the bot must do)

1. **Point-in-time or it cannot be used to test anything.** The archive revises team files **in place**. A backtest that reads
   today's file for a September game is look-ahead. Requirement on the archive side: the folder is a git repo, or every revision
   is kept, so any file can be read as of a date; `updates/` stays append-only. Bot side: the adapter only reads
   snapshots/commits dated before a game's as_of, the same contract as the NFL event store (DATA_LAYER.md).
2. **Claims, not prose.** A model cannot read a paragraph. The adapter extracts each material claim into a record: sport, team
   (and player id when named), layer, claim text, direction (helps/hurts what), what it affects (unit, scheme, availability,
   motivation…), source outlet and date, archive date first seen, confidence, and the archive file and line. Extraction is
   versioned; the claim keeps its source link. A machine-readable sidecar written by the archive would make this cheaper and
   less error-prone. Worth asking Muse for one.
3. **Reporter, not journalist, both ways.** The archive's own rule (sourced, no sway) carries into the bot: no claim enters a
   model unless it has a source and date. Unsourced or undated claims are dropped and counted.
4. **Read-only, one direction.** The bot never writes to the archive (the archive's rule too). Intake is a scheduled snapshot
   pull. It needs a runtime-registry entry and an alarm (ADR-0074) **when it is built**, not before.
5. **Application, tested like every other factor (ADR-0075).** A qualitative claim class reaches "applied" only through a
   pre-registered test against the market, the 77.2 yardstick included: is it real, already priced, or invisible? Muse's stated
   use for sentiment ("when a window opens or closes") is a timing hypothesis, and gets tested as one.

## Operator answers, 2026-10-15 22:18 PT (window recorded)

1. **Versioning: done.** The archive root is a git repo; every edit is committed, so any past date can be checked out.
2. **Claims: done.** `CLAIMS_SCHEMA.md` v1.0 is in the archive: one JSONL record per claim (team/player, layer, claim class, what it
   affects, direction, claim, source + source date, confidence, as-of date, source prose section). No claim without a source and
   a date. Backfill of all 96 files is queued, running one file at a time.
3. **Location:** `~/workspace/goals/external-witness-prediction-market-bot/files/nfl-archive/` on the operator's archive machine.
   It is portable by zip or git. **Not yet reachable by a terminal**; the operator will say when it should be pushed somewhere a
   terminal can pull from. The adapter waits for that.

## One caveat the adapter must carry (window)

Git history starts 2026-10-15. A claim's **source date** can be months earlier, but the archive chose which sources to keep in
October, already knowing how September went. So a backtest on games before the first commit carries **selection bias**, even if
every source date checks out. The adapter tags every claim with `first_committed`. Results on games before 2026-10-15 are
reported as exploratory and kept apart from results on claims committed before kickoff, which carry no such bias and start
accruing now.

## Open questions (for the operator, when the adapter is built)

- Where a terminal pulls the archive from (answer 3 above).
