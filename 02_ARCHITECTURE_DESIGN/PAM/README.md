# PAM: Player Attribute Matrix (ADR-0075 §3)

One sport-agnostic record, one append-only store, one read path `pam_as_of(sport, player_id, as_of)`. See `CORE_SCHEMA.md`. Operator, 2026-10-14: "we're gonna start piping in the PAM into the NFL, NBA, MLB and NHL (starting with NFL and NBA) - this is going to be a portion of our Syndicate32 bridging - it needs to stay dynamic enough that we can port it easily and do mass application but we'll keep it substantive for when it matters most."

## What exists (2026-10-14, W75.1)

| Sport | Core | Taxonomy | Mass tier | Deep tier | Stage |
|---|---|---|---|---|---|
| NBA | yes | `qualitative_data/pam/nba/taxonomy.json` (15 PRF, 32 modifiers, from the v4 docx) | none | 100 records (2 snapshots x 50, lossless port of the v4 CSVs; 002 supersedes 001) | aggregated |
| NFL | yes | `NFL_TAXONOMY.md` (9 groups); built group: WR (`qualitative_data/pam/nfl/taxonomy.json`) | WR, 2023-2025: 247 records | none (method proposed, `DEEP_TIER.md`) | aggregated (WR); interpreted/applied: none |
| MLB | core only | none | none | none | none |
| NHL | core only | none | none | none | none |

Nothing is applied: no engine reads PAM yet and no experiment script was rewired (they still read the old NBA CSVs).

## Layout
`src/prediction_market_bot/pam/` (schema, store, `nba_port`, `nfl_wr_mass`) · `scripts/pam_nfl_wr_mass.py` (offline run) · `qualitative_data/pam/<sport>/{taxonomy.json,records.jsonl}` · tests `tests/test_pam_core.py`, `tests/test_pam_nfl_wr.py` · WR run output `NFL_WR_MASS_REPORT.txt`.

## D5 line
**D5(a) cluster designs: NFL 0 -> 1 (core + 9-group taxonomy + WR mass classifier, aggregated), NBA 0 -> 1 (v4 ported losslessly into the core, deep tier), 2026-10-14, W75.1.** Gaps registered: GG-775..GG-779.

## The layered build for NFL, MLB and NHL (operator, 2026-10-21 07:40 PT)

> "I'm sure it makes sense why I'm letting Muse architect its database off of the NBA PAM archetype - since conceptually the level
> of depth that we're looking for aligns with that document. Do we have the structures in place for the other core 3 sports so that
> it can also work on them as well? A layered approach towards building PAMs for the other 3"

The NBA v4 document (15 archetypes, 32 modifiers, each defined) is the depth bar. Each sport is built in the same five layers. A
layer is only started once the one before it exists.

| Layer | What it is | Who builds it | NBA | NFL | MLB | NHL |
|---|---|---|---|---|---|---|
| 0. Core | the sport-agnostic record, store, `pam_as_of` | bot (done W75.1) | done | done | done | done |
| 1. Taxonomy at v4 depth | every archetype and modifier, defined, per position group | Claude drafts (a terminal block), Earl approves | done (v4 port) | **draft v1**: 9 groups (QB RB WR TE OL EDGE/DL LB CB S), signals named; no modifiers yet; below v4 depth | **none** | **none** |
| 2. Signal map | each archetype/modifier → the free metric and source that measures it, with seasons; NONE where nothing free does | Muse (scout), from the taxonomy | R-027 (queued) | partly in draft v1 + R-018 (PAM gaps) | after layer 1 | after layer 1 |
| 3. Mass tier | every player classified automatically from those signals, point in time | bot | none | WR only (247 records, 2023-25) | none | none |
| 4. Deep tier | the players who matter most, Earl + Claude, superseding mass records | Earl + Claude | 100 records (v4 snapshots) | none (scope: QB, WR, RB, TE, OL, core defenders) | none | none |

**So the answer at 2026-10-21:** Muse can work NBA now (layer 2). It can partly work NFL (draft v1 names the signals; R-018
covers the blocked ones). It cannot usefully work MLB or NHL until those sports have a layer-1 taxonomy. Until then, a Muse
ticket would be Muse inventing the archetypes, which is thinking, not scouting (charter v3). Next: one terminal block drafts NFL
to v4 depth (archetypes + modifiers for all 9 groups) plus first-draft MLB and NHL taxonomies, for Earl's approval. Then each
sport gets its Muse signal-map ticket.
