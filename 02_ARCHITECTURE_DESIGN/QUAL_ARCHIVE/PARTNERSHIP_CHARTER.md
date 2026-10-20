# Muse ↔ Claude operating protocol (charter v2, 2026-10-19)

**Status: IN FORCE, set by the operator, Earl.** v2 supersedes v1 (2026-10-15), which is kept verbatim at the bottom. Changing it
is Earl's call; the version line moves when it changes. A copy is pasted into Muse; this file is the one both sides read.

**Why v2 (operator, 2026-10-19 17:30-17:33 PT):** "Since I'm officially going to use it as a tactical operator for the project -
we'll need to build out actual protocol for it so that I'm not applying on the fly or making shit up as we go." ... "We're far
enough into the project that the compatible partnership with Muse isn't something we need to learn as we go - we can apply the
shit that we succeeded + failed at right now. We know what we're using it for. We know what its AI harness is capable of and what
it can't do effectively. We know what how we've structured our workflow and the project operations within our system (Claude). We
understand the gap(s) in between. Let's get it documented as we close out your window."

And what he told Muse the same evening: "the projects 'Granularity Index' is getting built as we speak. Your reporting arms will
be crucial in adding weight to the Granularity Index ... I'll have you run an aggregator to pull shit like [that] in for us to then
pipe into our architecture."

## 1. What we know (the evidence this protocol is built on)

| | Worked | Failed or limited |
|---|---|---|
| **Muse** | Mass aggregation fast: 2,059 sourced, dated claims across 99 files in one day (archive, 2026-10-15). Git discipline: pushes after every commit, no history rewritten (verified 90921e5 → 1fb38c1). Answered R-001..R-003 in minutes, bumped the claims schema additively (v1.1) and logged it. | As an unsupervised project manager it "has been failing consistently without handholding" (operator's trial, 2026-10-08). Runs only when the operator turns it on: R-004 and R-005 have sat unanswered since 2026-10-15 while it was on ice. Free-text fields ("Week 7", "2026-10-18 vs NYJ") are not joinable. An example name leaked into data (the "undervalued board"). Curated with hindsight: history starts 2026-10-15. |
| **Claude** (strategic window + terminals + cloud sessions) | Turns facts into tested verdicts (aggregation > interpretation > application, ADR-0075). Can recompute a stat from free data, test it against a market price, and watch the archive. Reaches the box through the box bridge (04_EXECUTION/BOX_TASKS/). | Runs in waves and windows, not continuously; the operator's weekly usage limits stop it. Cannot create repos or write the archive. Cloud sessions reach the open web only through allowed domains. |
| **Between them** | Two channels, no human relay: Muse writes STATUS.md in the archive; Claude writes TO_MUSE.md in the public bot repo. | Nothing in the bot consumes the archive yet (the adapter waits). A fact like "701st of 701" is unusable if its comparison group is not written down exactly. The watchdog runs only when a window is open. |

## 2. Roles

| Who | Is | Owns | Never |
|---|---|---|---|
| **Muse** | The tactical operator for **aggregation**: the reporting arm of the granularity index and the qualitative archive | Finding, sourcing and recording facts in `eignacio1/sports-intel-archive`: index facts (splits, ranks, records), availability and role news, the qualitative layers. Its own build order inside the tickets it is given. | Interprets a fact into a bet, a pick, odds or a model. Writes to the bot repo. Rewrites pushed history. Uses a paid source ($0 rule). Records a fact without a source and a date. Acts as the project's manager or governor. |
| **Claude** | Interpretation, application, verification, tasking, watchdog | Reading the archive read-only (pinned to a commit), recomputing facts, turning them into tested factors, issuing tickets (R-NNN), grading the archive's health, reporting verdicts back. | Writes to the archive. Changes Muse's schema or rules. Treats an archive claim as a fact before it is verified. |
| **Earl** | Strategic reviewer | Direction (sports, layers, priorities), breaking schema changes, disagreements between Muse and Claude, anything about money. Turning Muse on and off for usage. | Relaying files or messages between the two. |

The split follows the granularity index (`02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md`): an entry has five parts. **Muse brings
the first two** (the split, the rank against history); **the bot does the last three** (the matchup cross, the market map, the
application). Muse reports; it does not decide.

## 3. The index fact (what Muse records for the granularity index)

One JSONL record per fact, schema **v1.2** (additive to v1.1; nothing renamed or removed):

| Field | Required | Example (operator's, 2026-10-16) |
|---|---|---|
| `claim_class` | yes | `index_fact` |
| `sport`, `subject_type`, `subject` | yes | NFL, player, "Bo Nix" (as the team lists him) |
| `metric` | yes | average air yards per pass attempt |
| `split` | yes | the situation it is cut by, or `none` (e.g. "2nd half", "light box (<8)") |
| `value` | yes | 4.9 |
| `rank`, `population_n` | when ranked | 701, 701 |
| `population` | when ranked or compared | the comparison group written so it can be recomputed: "qualified QB seasons through 6 team games, 2006-2026, qualifier = ..." |
| `as_of` | yes | the date or game through which the fact holds |
| `source`, `source_url`, `source_time` | yes | publisher, link, publish time (ISO 8601) where given |
| `applies_to` | when game- or week-specific | nflverse `game_id` (`2026_07_NYJ_PIT`) or `season` + `week` as integers, plus the readable text |
| `confidence`, `notes` | optional | |

A fact without `population` cannot be ranked against anything, and a fact the bot cannot recompute stays REPORTED (section 5).

## 4. Tasking (how Muse gets its work)

- **Tickets come from the engine's gaps, not from Muse's curiosity.** Claude writes them in `TO_MUSE.md` as `R-NNN`, each with:
  the measure it serves (from CLAUDE.md's distance table), the exact metric/split/population wanted, allowed sources (free only),
  the deliverable path in the archive, and "done when".
- **Size:** one ticket fits one Muse work cycle. Larger work is split before it is sent.
- **Priority** is Claude's order in the file, unless Earl reorders it. Muse may propose a ticket in STATUS.md; Claude accepts or
  declines it in TO_MUSE.md.
- **Answer:** every R-NNN gets a STATUS.md reply and a commit naming it, in the next cycle Muse runs. Muse says "blocked" with the
  reason rather than going silent.

## 5. Verification (nothing enters a model unverified)

| Grade | Means | Can feed a model? |
|---|---|---|
| **VERIFIED** | The bot recomputed the fact (or its class) from free data and matched it, as 80.3 does for the run-box example | Yes, through the normal pre-registered test |
| **REPORTED** | Sourced and dated, not yet recomputed | No. Context and leads only |
| **FAILED** | Recomputed and did not match, or no source/date | No. Reported back to Muse with the difference |

A class is verified once (with a positive control), then spot-checked each wave. Claims about games before 2026-10-15 carry
selection bias (the archive was curated knowing how September went) and are exploratory only.

## 6. The loop back: application feeds aggregation

Once a fact class reaches a price, Claude posts its verdict in TO_MUSE.md: **REAL-NOT-PRICED** (the market missed it), **REAL-AND-
PRICED**, **INVISIBLE**, or **NOT REAL**. Muse digs deeper where the verdicts are REAL-NOT-PRICED and stops spending effort where
they are NOT REAL. Standing direction (operator, 2026-10-16): "beating buddy off his phone placing parlays, that's the first step" -
so props, player-level and thin-market facts come before headline team ratings, which the market already prices.

## 7. Cadence

| When | Muse | Claude |
|---|---|---|
| In season, weekly per sport | Deltas for every team (`updates/`, append-only); answer open tickets | Read at each wave close; new tickets from the index gaps |
| Injury-report windows (NFL Wed-Fri and inactives; NBA game days) | Availability and role facts with `source_time` and `applies_to` | Join them point-in-time |
| Muse on ice (operator's call) | Nothing; the queue waits | Tickets keep their order; the sitrep shows how long each has waited |

## 8. The watchdog (Claude, every wave close)

Pushes flowing (last commit age, commits since last wave) · every record parses and matches the declared schema version ·
no pushed history rewritten (the last commit seen is still an ancestor) · duplicates and contradictions (reported, not resolved) ·
staleness for in-season teams · ticket age (an R-NNN open more than 72 h while Muse is running is flagged in the sitrep) ·
the VERIFIED/REPORTED/FAILED counts per class. Findings go to TO_MUSE.md; only Earl-level questions go to Earl.

## 9. What goes to Earl (and only this)

A new sport or layer, or what L3 should be · a breaking schema change (a major version) · priorities when Muse and Claude disagree
· anything about money, paid sources or real capital · Muse on or off for usage · one line per wave in the sitrep: what moved on
both sides.

## 10. Standing rules

1. **Reporter, not journalist**, on both sides. An interpretation from the archive is never treated as a fact.
2. **Point in time.** History is never rewritten; a correction is a new commit. Claude reads pinned to a commit and tags every
   claim with its first commit.
3. **Schema versions.** Additive changes bump the minor version and are logged in STATUS.md; a breaking change waits for Earl.
   Claude's adapter pins the version it reads.
4. **Names are the operator's.** Example names never become field values (the "undervalued board", not the earlier example name).
5. **No secrets** in either repo, file or message. The deploy key is write-scoped to the archive repo and revocable.
6. **$0.** Neither side adds a paid service.

---

## v1 (2026-10-15), superseded 2026-10-19 — kept verbatim

**Set by the operator, Earl, 2026-10-15 22:56 PT:** "a directive on how this partnership will work - essentially automation on
both ends with me being the strategic reviewer for everything." Roles: Muse builds the archive (`eignacio1/sports-intel-archive`:
layers, claims, sourcing, build order within Earl's direction; never writes to the bot repo, places bets, picks or odds, or rewrites
pushed history); Claude reads the archive read-only, pinned to a commit, turns claims into tested factors and watches the archive's
health (never writes to the archive or changes Muse's rules or schema); Earl directs (new sports or layers, L3, breaking schema
changes, priorities when the two disagree, anything touching money) and never relays files. Channels: Muse → `STATUS.md` in the
archive (append-only, dated, replies by request id); Claude → `TO_MUSE.md` in the bot repo, read over HTTPS
(`https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/TO_MUSE.md`), entries
`R-NNN`, answered in STATUS.md and closed by a commit naming them. Loop: Claude reports what each claim class did at a price
(REAL-NOT-PRICED / REAL-AND-PRICED / INVISIBLE / NOT REAL); Muse digs where it pays. Watchdog each wave: pushes flowing, claims
parse with source and date and current schema, no history rewritten, duplicates and contradictions reported, staleness. To Earl
only: new sport/layer/L3, breaking schema change, disagreements, money/paid/capital, a short digest each wave. Rules: reporter not
journalist; point in time (claims about games before 2026-10-15 exploratory); schema versions (breaking waits for Earl); no
secrets; $0.
