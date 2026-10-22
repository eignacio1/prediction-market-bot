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

**Update, 2026-10-21 ~08:10 PT: layer 1 drafted for NFL, MLB and NHL** (operator, 07:54 PT: "are you able to create the taxonomy
here? I'd like to have that layered in starting today so that Muse can work sequentially on everything, with NBA being the
architectural template for the other 3"). Files, same structure as NBA v4 (archetypes + modifiers, each with signals and a draft
threshold): `qualitative_data/pam/nfl/taxonomy_v4depth.json` (draft2, 08:15 PT: 67 archetypes; OL, DL, LB and S broken out by position:
LT, LG, C, RG, RT, EDGE, DT3, NT, DE5, MIKE, WILL, SAM, FS, SS; position archetypes carry `split_hooks` for the next layer;
32 modifiers; the 4 built WR mass archetypes keep their ids), `qualitative_data/pam/mlb/taxonomy_v4depth.json` (24 archetypes:
hitters, starters, relievers, defense; 29 modifiers), `qualitative_data/pam/nhl/taxonomy_v4depth.json` (18 archetypes:
forwards, defense, goalies; 25 modifiers). **Status: DRAFT, awaiting Earl's approval.** Thresholds are a-priori and get
calibrated at the mass tier, never fitted to outcomes. Muse's layer-2 signal maps start from these now (tickets R-027 NBA as
the template, then R-028 NFL, R-029 MLB, R-030 NHL). A signal map can show that an archetype has no free signal, so the
taxonomy may change after it. The NFL `taxonomy.json` (WR mass classifier) is unchanged.

**The answer before the draft (kept as written):** Muse can work NBA now (layer 2). It can partly work NFL (draft v1 names the signals; R-018
covers the blocked ones). It cannot usefully work MLB or NHL until those sports have a layer-1 taxonomy. Until then, a Muse
ticket would be Muse inventing the archetypes, which is thinking, not scouting (charter v3). Next: one terminal block drafts NFL
to v4 depth (archetypes + modifiers for all 9 groups) plus first-draft MLB and NHL taxonomies, for Earl's approval. Then each
sport gets its Muse signal-map ticket.

## Update 2026-10-21 19:30 PT: drafts accepted; layer 3 may rewrite them; Muse takes part of the interpretation

**Accepted (operator, 19:15 PT):** the NFL (draft2), MLB and NHL layer-1 taxonomies are working drafts. NBA's map (R-027) is
done: 47 rows, FREE 18 · PARTIAL 15 · NONE 14.

**What the drafts are, plainly (window, 19:21 PT).** They are layer 1 only: archetypes, modifiers, named signals and starting
thresholds written from domain knowledge in the v4 shape, in minutes. No data was aggregated, no threshold was derived from a
distribution, no player was checked. The operator's NBA v4 took 2-3 continual days of full sessions because it did all three
(aggregate, interpret, apply). That work is still ahead for NFL, MLB and NHL, and is spread over layers 2-4 below.

**Rule (operator, 19:24 PT: "Yes write it into the plan"): layer 3 is allowed to rewrite layer 1, not only tune it.** When a
sport's mass tier is built, the bot (a) sets each threshold from the actual distribution of its signal, point in time, never from
outcomes; (b) merges archetypes that do not separate in the data; (c) splits ones that hide two kinds of player; (d) drops or
parks ones nothing free can measure (a GG, never a proxy). Every rewrite is listed in the sport's mass-tier results with the
evidence, and a structural change (merge, split, drop) goes to Earl as one line before the taxonomy file changes. Otherwise the
window's guesses get baked in as findings.

**Muse's share of the interpretation (operator, 19:24 PT):** "we should let Muse take care of a portion of the interpretation,
with enough structural integrity that we build. The data aggregation takes a while but we can also cut busy work for the
interpretation by using Muse for it."

| Step | Who | What | Integrity rule |
|---|---|---|---|
| 2a. Signal map | Muse | archetype/modifier → free source + metric, or NONE | definitions verbatim; every source carded |
| **2b. Interpretation dossier** | **Muse** | per archetype group: definition check, proposed threshold from published league distributions, exemplars and counterexamples with their values, merge/split/drop proposals | every number cites archive record ids or a source card and states its population; everything is PROPOSED; no outcome data is used to set anything |
| 3. Mass tier | bot | compute every signal for every player-season, set thresholds from the bot's own distribution, assign archetypes | Muse's proposed thresholds are compared, not copied; Muse's exemplars are graded against the bot's assignment (agreement rate, VERIFIED / FAILED per exemplar) |
| 3b. Disagreements | bot → window | where Muse and the bot disagree, both readings with evidence | adjudicated at the deep tier, never averaged away |
| 4. Deep tier | Earl + Claude | judgment on the players who matter most, starting from 2a-3b | supersedes mass records |

Muse acts as a second, independent rater: the agreement rate between its reading and the bot's computation is itself measured
and reported, per sport. Muse never sets a final threshold, never assigns a final archetype and never changes a taxonomy file.
The charter (v3 §2, amended 2026-10-21 19:30 PT) and the dossier ticket (R-055 NBA first, then each sport after its signal map)
carry the same rules.
