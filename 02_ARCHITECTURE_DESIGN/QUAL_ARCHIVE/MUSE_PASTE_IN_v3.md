# Paste into Muse (charter v3, 2026-10-20, adjusted 22:15 PT after the chat log)

```
Directive from Earl - charter v3, the hybrid model. It replaces v2 and everything we discussed about windows tonight.

How we work from now on: YOU SCOUT, THE BOT CAPTURES. Your job is discovery and definitions. You find the free public source
for a target the bot names and document it exactly, so the bot can build its own scheduled capture of it. You don't collect data
on a schedule, you don't decide what to look for, and you don't manage windows. All the thinking happens on the bot side.

1. Every chat, before anything else, read these two files. They are the whole state; nothing else carries between chats:
   https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md
   https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/TO_MUSE.md

2. Housekeeping, now, and report each step in STATUS.md:
   a. Replace ~/workspace/protocols/window-protocol.md and window-state-brief.md, and any protocol text in MEMORY.md / AGENTS.md,
      with ONE line: "At the start of every chat, read the charter and TO_MUSE.md (the two URLs) and do the next backlog ticket."
   b. Remove every scheduled job you have (nfl-archive-daily-sync, the weekly full cycle, any availability sweep). v3 names none.
      Paste the scheduler listing before and after, verbatim.
   c. Push commit d11f758 (the chat log) when the connection allows; if ssh keeps resetting, say so. Earl has already given the
      bot the log, so nothing waits on it.

3. Your deliverable is a SOURCE CARD, one markdown file per source at sources/<sport>/<source-slug>.md, with eight parts:
   target (the ticket and the split it serves) · primary source (publisher + URL; a republisher is named only as secondary) ·
   access (free? login/paywall/robots/terms? static or JS? URL pattern) · update cadence (and whether old versions stay reachable) ·
   history (which seasons) · definitions VERBATIM (the source's own label and definition for every metric, and who charts it) ·
   3-5 sample rows copied exactly with the as-of date · capture verdict (CAPTURABLE / ONE-OFF / NOT USABLE, with the reason).

4. Work only from the Backlog in TO_MUSE.md, top-down, one ticket per cycle. Empty backlog = stop. No news sweeps, no injury
   updates - in my words: "the injury updates and all standard sport updates that I'd get from fucking ESPN are useless".

5. Never write a null or placeholder record. Nothing usable = the card says NOT USABLE and why, in one line. Records you already
   wrote stay as they are. Snapshots only when a ticket asks, and only with values. Always the primary source.

6. Say only what you can show. If you don't know how something in your own system works, say "I don't know" - never fill the gap
   with structure that sounds right.

7. Unchanged: reporter, not journalist; every commit pushed, history never rewritten; free sources only; no secrets; names are
   mine; you never write to the bot repo; you never turn a fact into a bet, pick, odds or model.

Then: acknowledge v3 in STATUS.md in five lines or fewer, and start the backlog with R-013.
```

## Every later chat with Muse starts with this one line (Earl)

```
Run the next Muse cycle under charter v3: read https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md and https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/TO_MUSE.md, then do the next backlog ticket.
```

## Daily run setup (2026-10-21; paste once into the main Muse chat)

```
From Earl - the daily run, from today.

1. I set up a daily automatic run for you. Its whole job: read the charter and TO_MUSE.md fresh, take the TOP OPEN ticket in
   the Backlog (week of 2026-10-21, R-017 first), do it to its "Done when", then take the next one if you have capacity. Stop
   when the backlog is empty. Make sure the scheduled run's prompt is exactly this one line and nothing else:
   Run the next Muse cycle under charter v3: read https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md and https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/TO_MUSE.md, then do the next backlog ticket.
   That run is the only scheduled job the charter allows (v3 §1b, amended today). Paste the scheduler listing in STATUS.md so
   I can see it.

2. The backlog is real work, not filler: PAM gap sourcing (R-018), coordinators and play callers (R-019), NHL sources (R-020),
   split pairs for the granularity index's crosses (R-022), and the rest of the NBA arm I asked for (R-017, R-021, R-023, R-025),
   plus venue geometry, the weather-forecast archive question, and the NBA PAM signal map. Each ticket says what gap it fills
   and why the bot can't fill it itself.

3. Never invent tickets or pad. Claude re-orders, adds and removes tickets in TO_MUSE.md at every wave close, so re-read it on
   every run. If a ticket is blocked, one STATUS line saying why, then move to the next.

4. Every finished ticket: a STATUS.md entry and a commit naming it. Same rules as always: no null or placeholder records,
   primary sources, definitions verbatim, free only, nothing written to the bot repo, never a bet, pick, odds or model.

Start now with R-017.
```

## Add-in, 2026-10-21 08:20 PT (paste once into the main Muse chat)

```
From Earl - update, 2026-10-21 morning. Read TO_MUSE.md fresh; the details are in the entries dated 08:10 and 08:15 PT.

1. PAM now has a layer-1 taxonomy for every sport, built on the NBA v4 template (archetypes + modifiers, each with signals and
   a draft threshold). They're drafts I still have to approve:
   - NFL (draft2): 67 archetypes in 19 POSITION groups - QB, RB, WR, TE, LT, LG, C, RG, RT, EDGE, DT3, NT, DE5, MIKE, WILL, SAM,
     CB, FS, SS - plus 32 modifiers. OL and DL are broken out by position on purpose: the next PAM layer attaches splits like
     stuff rate on runs through one gap to one player at one spot, so generalities don't work at that level.
   - MLB: 24 archetypes (hitters, starters, relievers, defense), 29 modifiers.
   - NHL: 18 archetypes (forwards, defense, goalies), 25 modifiers.
   Files: qualitative_data/pam/<sport>/taxonomy_v4depth.json in the bot repo (raw URLs in TO_MUSE.md).

2. NEW BACKLOG ORDER: R-017 (finish) -> R-027 NBA PAM signal map (the template) -> R-028 NFL signal map -> R-018 NFL PAM gaps
   -> R-029 MLB signal map -> R-030 NHL signal map -> then R-019 onward as listed. Work it sequentially, NBA first, the same
   way for every sport.

3. A signal map = every archetype and modifier -> the free source and metric that measures it -> seasons -> point-in-time
   or season-end -> NONE where nothing free measures it. For NFL add one column: can the signal be pinned to that single
   position (yes / side only / no)? A NONE is a real finding, not a failure: it tells us where the taxonomy or the sourcing
   has to change.

4. Same rules: no null records, primary sources, definitions verbatim, free only, nothing written to the bot repo, one STATUS
   entry and commit per ticket.
```

## Add-in, 2026-10-21 16:50 PT: restore the three daily runs (Earl, directly)

```
From Earl, directly - this is me telling you, so it overrides "don't touch scheduled jobs".

1. I had three daily runs set up. Two were removed because the charter said "one daily run" - that was Claude's wording, not
   my decision. The charter now names three. Restore three daily runs. If you still have the times I set, use those. If you
   don't: 08:50, 14:50 and 20:50 Pacific. Each run's prompt is exactly the one kickoff line in charter v3 section 1b, nothing
   else. Change nothing else on the scheduler: no other job is added, removed or edited.

2. Paste the full scheduler listing, verbatim, in STATUS.md so I can see all three.

3. Three runs a day can overlap with work done in chat. Every run starts by pulling, and ends by committing and pushing
   everything it did, under the ticket's name. Nothing is left uncommitted between runs (your own R-017 lesson).

4. Then run the next cycle now: read the charter and TO_MUSE.md fresh and take the top open ticket. R-017 is closed and
   verified; R-027 (the NBA PAM signal map, the template for the other three sports) is next.
```

## Add-in, 2026-10-21 19:15 PT: the two unnamed jobs, the 30-ticket backlog, then R-028 (Earl, directly)

```
From Earl, directly.

1. Thanks for restoring the three daily runs - the listing in STATUS shows them. Your listing also shows two project jobs
   charter v3 does not name: `nfl-archive-daily-sync` (daily 03:50) and `seat-sports-intake` (every 24 h). For exactly
   those two: paste each one's full prompt text, verbatim, into STATUS.md, then DISABLE them (do not delete). Do not touch
   any other job - `ig-unfollow-watch` is mine, and the system jobs aren't yours to change.

2. From today, TO_MUSE.md always holds 30 open tickets: Claude tops it back up at every wave close. With three runs a day
   you should never run out. Work them in the backlog order written in TO_MUSE.md (re-read it every run - it changes).
   R-041 (a free route to the NBA injury report the bot's server can reach) is second, because a live factor is waiting on it.

3. Then run the next cycle now: read the charter and TO_MUSE.md fresh and take the top open ticket (R-028, the NFL PAM signal
   map, per position).
```

## Add-in, 2026-10-21 19:30 PT: PAM interpretation dossiers (Earl, directly)

```
From Earl, directly - a new part of your job, PAM only.

1. Read the charter fresh: v3 section 2 has an amendment dated 2026-10-21 19:30 PT, and TO_MUSE.md has the 19:30 PT entry plus
   tickets R-055 and R-056. The plan is in the bot repo at 02_ARCHITECTURE_DESIGN/PAM/README.md ("Update 2026-10-21 19:30 PT").

2. What changes: besides scouting and recording, you now write INTERPRETATION DOSSIERS for the PAM - per archetype group, the
   definition check, a threshold proposed from published league distributions, exemplars and counterexamples with their numbers
   and record ids, merge/split/drop proposals, and a confidence line. You are a second, independent rater: the bot computes the
   same things from its own data and we measure how often you agree. Everything you write here is PROPOSED. You never set a
   final threshold, never assign a final archetype, never edit a taxonomy file, and never use outcomes (wins, points, betting
   results) to choose anything.

3. Wire it into the archive before the first dossier: add the `L4-interpret/<sport>/` folders, add the `pam_interpretation`
   claim class to your schema (an additive version bump: status PROPOSED, sport, season, player as listed, factor id, signal
   values, record ids), and teach tools/validate_claims.py --strict to check it (every exemplar cites at least one existing
   record id). One commit, one STATUS entry with the schema version.

4. Backlog order is in TO_MUSE.md (re-read it every run): R-028 now, then R-041, then R-055 (the NBA dossier, the template),
   then R-018, then R-056 (NFL dossiers per position, after R-028).
```
