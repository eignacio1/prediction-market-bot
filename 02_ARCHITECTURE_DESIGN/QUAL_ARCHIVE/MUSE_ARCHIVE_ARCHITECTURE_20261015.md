# Sports Intelligence Archive — Architecture Synopsis
**Status:** NFL base complete (Oct 15, 2026). NBA/NHL/MLB queued.
**Purpose:** Multi-layered qualitative intelligence on every team in the core four sports — the "obvious to insiders" systematized into a queryable, procedural format that a prediction-market decision system can consume.

---

## Layer Stack

Layers build upward. Each layer assumes the ones below it and adds a distinct dimension. Nothing is duplicated across layers — each answers a different question.

| Layer | Question it answers | Source depth | Files |
|---|---|---|---|
| [L1-foundational](L1-foundational/) | *What is this team?* Org mapping (owner → kitchen), personnel, scheme identity, coaching, trajectory, undervalued watch, insider-obvious signals. 7 sections per team. | Beat writers, press conferences, interviews, org reporting | 32/32 |
| [L2-schematic](L2-schematic/) | *How does this team actually play?* Offensive/defensive scheme mechanics, coordinator fingerprints, matchup levers (sourced rates), in-season evolution. 5 sections per team. | Film analysts, scheme writers, coordinator histories | 32/32 |
| [team-news](team-news/) | *What are insiders saying right now?* Key podcasts (3-5/team), last-30-days episodes with takeaways + sentiment, beat reporter roundup, insider-vs-public divergences, 30-day sentiment trajectory. | Team podcasts, beat writers | 32/32 |
| [cross-team](cross-team/) | *What aggregates across teams?* Puka board (128 undervalued flags), trajectory index (32 teams condensed), league trends (8 patterns, 3+ team bar), 8 division summaries. | Synthesis of L1+L2+team-news | 11/11 |
| [updates](updates/) | *What changed?* Dated deltas. New intel lands here; team files revised in place. Append-only history. | Intake cycles | — |
| L3 (queued) | *Deeper.* Direction TBD after base review. | — | — |

**Planned sports:** `nba-archive/`, `nhl-archive/`, `mlb-archive/` — same layer stack, same contracts.

---

## Folder Network

```
nfl-archive/
├── README.md                  # What it is, how it's built, deployment, rules
├── INDEX.md                   # Master nav — every team, every layer, one page
├── MANIFEST.md                # Coverage tracker — what's done/in-flight/missing
├── ARCHITECTURE.md            # This file
├── L1-foundational/           # 32 teams ÷ 8 divisions — org + 5 buckets + insider-obvious
│   ├── nfc-east/  nfc-north/  nfc-south/  nfc-west/
│   └── afc-east/  afc-north/  afc-south/  afc-west/
├── L2-schematic/              # 32 teams ÷ 8 divisions — scheme mechanics + levers
│   └── (same 8 divisions)
├── team-news/                 # 32 teams ÷ 8 divisions — podcasts + beats + sentiment
│   └── (same 8 divisions)
├── cross-team/
│   ├── undervalued-watch.md   # THE PUKA BOARD — 128 flags, by position, sourced
│   ├── trajectory-index.md    # 32 teams condensed, insider-obvious signals
│   ├── league-trends.md       # 8 cross-team patterns (3+ team bar)
│   └── division-summaries/    # 8 files — condensed teams + division dynamics
├── updates/                   # Dated deltas (YYYY-MM-DD.md)
└── web/
    └── index.html             # Static click-through nav page
```

---

## Data Contracts

Every file in a layer follows the same section schema. A consumer system can parse deterministically.

**L1 team file** (`[team].md`): Organization | Personnel | Scheme | Coaching | Trajectory | Undervalued watch | What's obvious to insiders but invisible in the numbers
**L2 team file** (`[team].md`): Offensive scheme | Defensive scheme | Coordinator fingerprints | Matchup levers | Evolution
**team-news file** (`[team]-news.md`): Key podcasts | Recent episodes (date/title/takeaways/sentiment+quote) | Beat reporter roundup | Insider-vs-public divergences | 30-day sentiment trajectory
**Puka board** (`undervalued-watch.md`): entries by position — player, team, reason, source. No recommendations.
**Trajectory index** (`trajectory-index.md`): 2-3 lines per team, by division, cited.
**League trends** (`league-trends.md`): trend name, teams exhibiting (3+), evidence per team, near-misses logged separately.

---

## Integration Surface (for the consumer system)

The archive is read-only data. The bot project never writes here.

- **Puka board → prospect watch:** undervalued flags feed the prospect/undervalued pipes. Each entry has the mechanism (why unpriced), not just the name.
- **Trajectory index → cell routing:** insider-obvious signals map to `(market_type, band)` cells via the seat's cell-routing template. A trajectory shift in a team's offense touches that team's T1/T4 cells.
- **League trends → structural priors:** cross-team patterns (e.g. under-center installation wave across 10 teams) inform league-wide assumptions, not single-team bets.
- **team-news sentiment → timing:** sentiment trajectory signals *when* a window opens or closes, not *what* to do about it.
- **updates/ → refresh cadence:** dated deltas let the consumer diff what changed without re-reading 96 files.

---

## Growth Vectors

1. **L3** — deeper layer, direction TBD after base review.
2. **NBA / NHL / MLB archives** — same stack, same contracts, sport-specific buckets (e.g. MLB: rotation/lineup/park factors; NBA: rotations/PRF shifts; NHL: goalie-centric).
3. **updates/ cadence** — weekly deltas during season, daily during high-leverage windows (trade deadline, playoffs).
4. **Artifact app** — live browsable front-end (exists as `nfl-archive` artifact; currently affected by a platform web-serving bug, tracked with Muse team).

---

## Operating Rules (load-bearing)

- Intelligence only. No bets, no picks, no odds, no game predictions.
- Every material claim sourced (outlet + date). Unverifiable = cut.
- **Reporter, not journalist.** Cite interpretations WITH exact source attribution. Never adopt, extend, or sway toward a narrative. Completely unbiased, no sway either direction.
- **Build methodology:** components sequentially, not parallel batches. Large ambiguous clusters validated against PDTP (multi-pass, adversarial, confidence-graded) before landing.
- Plain language. Jargon explained on first use.
- Append-only history: updates preserve what changed and when.
