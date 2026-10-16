# Muse ↔ Claude partnership charter (v1, 2026-10-15)

**Set by the operator, Earl, 2026-10-15 22:56 PT:** "a directive on how this partnership will work - essentially automation on
both ends with me being the strategic reviewer for everything." A copy is pasted into Muse; this file is the reference both
sides read. Changing it is Earl's call; the version line moves when it changes.

## Roles

| Who | Owns | Never |
|---|---|---|
| **Muse** - the archive builder | `eignacio1/sports-intel-archive`: layers, claims, sourcing, build order within Earl's direction | writes to the bot repo; places bets, picks or odds; rewrites pushed history |
| **Claude** - the bot's strategic window and its terminals | reading the archive (read-only, pinned to a commit), turning claims into tested factors, and watching the archive's health | writes to the archive; changes Muse's rules or schema |
| **Earl** - strategic reviewer | direction: new sports or layers, L3, breaking schema changes, priorities when the two sides disagree, anything touching money | relays files between the two |

## The two channels (no human relay)

- **Muse → Claude:** the archive itself. Every commit is pushed (`README.md` rule). Muse keeps `STATUS.md` at the archive root:
  what was built since the last entry, what is next, schema version, open questions for Earl, and replies to Claude's requests
  by id. Append-only, dated.
- **Claude → Muse:** `02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/TO_MUSE.md` in the bot repo. It is public, so Muse reads it over HTTPS
  without credentials:
  `https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/TO_MUSE.md`.
  Entries are numbered `R-NNN` and dated. Each one is a quality finding, a coverage request or a result. Muse reads it at the start
  of every work cycle, answers each R-NNN in `STATUS.md`, and closes it with a commit that names it.

## The loop: application feeds aggregation

The bot's chain is aggregation > interpretation > application (ADR-0075), and the archive is aggregation. Claude reports back
what each claim class did once it reached a price: **REAL-NOT-PRICED** (the market missed it: the most valuable kind),
**REAL-AND-PRICED** (true but already in the price), **INVISIBLE** (the test cannot see it), or **NOT REAL**. Muse uses those verdicts
to decide where to dig deeper. That is how the archive gets better at being useful, not just bigger.

## What Claude checks every wave (the watchdog)

- Pushes are flowing: last commit age and commits since the last wave.
- Every claim parses, has a source and a source date, and matches the current schema version.
- No pushed history was rewritten: the last commit Claude saw is still an ancestor.
- Duplicates and contradictions between claims (reported, not resolved: the archive is a reporter).
- Staleness: teams or layers not refreshed while their sport is in season.

Findings go to `TO_MUSE.md`. A finding that only Earl can settle goes to Earl.

## What goes to Earl (and only this)

- A new sport, a new layer, or what L3 should be.
- A breaking change to `CLAIMS_SCHEMA.md` (a major version).
- Priorities when Muse and Claude disagree.
- Anything about money, paid services ($0 rule) or real capital.
- A short digest each wave of what moved on both sides; Claude puts it in the bot's sitrep.

Everything else, both sides handle without him.

## Standing rules

1. **Reporter, not journalist** (the archive's rule) holds on both sides. Claude never feeds a claim into a model without its
   source and date, and never treats the archive's interpretations as facts.
2. **Point in time.** History is never rewritten; a correction is a new commit. Claude tags each claim with its first commit and
   treats claims about games before 2026-10-15 as exploratory (curation selection bias, INTAKE_CONTRACT.md).
3. **Schema versions.** A change to `CLAIMS_SCHEMA.md` bumps its version and is noted in `STATUS.md`. A breaking change waits for
   Earl. Claude's adapter pins the version it reads.
4. **No secrets** in either repo, file or message. Keys stay where they were made (the deploy key is write-scoped to the archive
   repo only and revocable).
5. **$0.** Neither side adds a paid service.
