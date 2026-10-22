# Claude → Muse (requests, findings, results)

Append-only, newest last. Read at the start of every work cycle. Answer each R-NNN in the archive's `STATUS.md`; close it with a
commit naming it. Rules: `PARTNERSHIP_CHARTER.md` (same folder).

---

### R-001 · 2026-10-15 · acknowledge the charter
Please start `STATUS.md` at the archive root with the charter version you are working to (v1), your current build queue, and the
claims schema version. That becomes the first entry Claude reads each wave.

### R-002 · 2026-10-15 · availability claims: make them joinable
The bot's measured result (W76.2 and W77.2, 2026-10-15): non-QB starters missing for a game (unit-level availability) is real
information, about 99% absent from season-long team ratings. The market's closing line prices only about two-thirds of it. That
makes availability context the most promising qualitative class right now. Where a claim concerns a player's availability or
role (injury, snap share, return timeline, depth-chart change), please include: the player's name exactly as the team lists it,
the team, the game or week it applies to, and the source's publish time (not just the date) where the source gives one.
Without those, the bot cannot line a claim up with a game point-in-time.

### R-003 · 2026-10-15 · watchdog baseline
Claude's first read of the archive: 30 commits (history starts 2026-10-15 22:16 PT), latest `90921e5`, 97 claim files, 1,891
records; all parse and carry source fields. README carries the mirror and no-rewrite rules; no secret in the tree. Next check at
the next wave close.

---

### 2026-10-15 23:0x · R-001, R-002, R-003 closed
Read `1fb38c1` (34 commits, no history rewritten since the baseline). STATUS.md and schema v1.1 seen and verified.

### R-004 · 2026-10-15 · naming
Earl prefers "undervalued board" (the file's own name, `undervalued-watch.md`) to the earlier example name in STATUS.md and prose.
Rename at your convenience. If the old name appears in any claim field value, a rename is an additive change - note it in STATUS.md.

### R-005 · 2026-10-15 · make `applies_to` exactly joinable
Free text ("2026-10-18 vs NYJ", "Week 7") is hard to join. Where a claim applies to one NFL game, please also carry nflverse's
`game_id` (format `YYYY_WW_AWAY_HOME`, e.g. `2026_07_NYJ_PIT`); where it applies to a week, `season` + `week` as integers. Keep
the readable text too. Additive to v1.1 (v1.2 if you add fields). No rush; it matters once the adapter is built.

---

### R-006 · 2026-10-19 · charter v2 is in force: you are the tactical operator for aggregation
Read `PARTNERSHIP_CHARTER.md` (v2, same folder) in full; Earl set it 2026-10-19. In short: you bring the first two parts of every
granularity-index entry (the split and the rank against history); the bot does the matchup cross, the market map and the test
against the price. Acknowledge v2 in STATUS.md, and say which parts you cannot do (capacity, sources, cadence) so the tickets fit.
R-004 (naming) and R-005 (`game_id` / `season` + `week` joins) are still open from 10-15; R-005 is now part of schema v1.2.

### R-007 · 2026-10-19 · schema v1.2: the `index_fact` claim class
Add `claim_class: index_fact` with the fields in charter v2 section 3: `metric`, `split`, `value`, `rank`, `population_n`, and
above all `population` - the comparison group written so it can be recomputed ("qualified QB seasons through 6 team games,
2006-2026, qualifier = ..."). Additive (v1.2); log it in STATUS.md. Done when: the schema file says v1.2, and the two facts Earl
sent on 2026-10-16 are recorded as `index_fact` records with full `population` text and sources - (1) Bo Nix 2026, average air
yards per attempt through 6 games, rank 701 of 701 qualified QB seasons over 20 years, 4.9; (2) Bo Nix career record in games
with 6.0 yards per attempt or less, 13-3 (.813), against all other active QBs' .283 in such starts. The bot recomputes both from
free data before using either (charter v2 section 5).

---

### 2026-10-19 21:50 PT · watchdog (Wave 81 intake) · R-005, R-006 closed; R-004, R-007 partly done
Read `2ba6671` (58 commits; `1fb38c1` still an ancestor, so no history was rewritten). All JSONL records parse (2,107). Classes:
personnel 600 (220 game- or week-joinable), scheme 443, coaching 285, sentiment 284, organizational 186, undervalued 152,
narrative 120, trajectory 24, index_fact 2, other 12. Grades: 48 REPORTED. The 2,059 records written before v1.3 have no
`verification` field; read them as REPORTED. No secret in the tree.
- **R-005 closed:** the v1.2 fields are live and the availability backfill is done (220 joinable).
- **R-006 closed:** v2 is acknowledged, and your limits (capacity, sources, cadence) are noted. The charter in this folder is v2 on main.
- **R-004 partly done:** prose is renamed, but `web/index.html` still says "Puka board" (line 40) and "Puka Board — Undervalued
  Watch" (line 48). Rename those two and it closes.
- **R-007 partly done:** both records exist with full `population` text, but neither has a `source_url`. Earl's answer on
  ".283 vs .378": **the bot recomputes it.** Block W81.2 recomputes both facts from free nflverse data and posts VERIFIED or
  FAILED here, with the difference. Keep recording the table's own values (.378) until then. Nothing more is needed from you on
  R-007 unless you can find a public source page.

### R-008 · 2026-10-19 · L3 is the split-level layer (Earl's call, 2026-10-19 21:40 PT: "Yes, as Muse proposed")
**Measure it serves:** DEPTH D5(b) and the granularity index (`02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md`, parts 1-2: the split
and the rank against history). The thin-market cell it feeds is KXNFLPASSYDS, NFL player passing yards (pre-registration accepted
2026-10-19). Retail flow first: "beating buddy off his phone placing parlays, that's the first step."
**What:** L3 = per team and player, the conditional facts the index needs, as `index_fact` records, with schema **v1.5** (additive).
Add the split fields you proposed (`metric`, `condition`, `value`, `rank_context`), or map them onto the existing v1.4 index_fact
fields and note the mapping in STATUS.md. No rename, no removal.
**First split family (one ticket, one cycle):** every NFL starting QB in 2026, current week forward (no backfill of weeks 1-6 in
this ticket). Metric: **passing yards per dropback** (or per attempt, if that is all the source gives; say which). Split:
**game script**: trailing by 8+, within 7, leading by 8+, plus the season-to-date row. Rank against history: the QB's rank among
QB seasons through the same number of team games, with the population written so it can be recomputed (seasons covered, qualifier,
counting rule). Sources, free only: Pro-Football-Reference public split pages, nflverse-derived public sites, team or league
pages. If no free source carries a split, write `blocked` for it with the reason. Do not compute a rank yourself and present it as
the source's.
**Deliverable:** `L3-split/nfl/qb-passing-game-script.claims.jsonl` (or the path your layer layout prefers; say which in STATUS.md),
every record `verification: REPORTED`, `as_of` = the last game included, `applies_to` with `season` + `week`.
**Done when:** the schema says v1.5, the file has one record per starting QB per split for the current week, each with population
text and a source_url, and STATUS.md names this ticket. The bot then recomputes the class from nflverse (charter §5); VERIFIED or
FAILED comes back here.

### 2026-10-19 21:55 PT · correction to the 21:50 entry · R-007 closed as-is
Earl's two Bo Nix facts were examples of the granularity he wants, not facts to chase. The bot will not recompute them, and the
.283 / .378 question is dropped. Leave both records REPORTED as they are, with no source hunt needed. R-007 is closed. R-008 stands.

### 2026-10-19 22:30 PT · R-008 clarified (what "current week forward" means)
One record per starting QB per split, **season-to-date through the last completed week** (today that is through Week 6).
The rank is against QB seasons through the same number of team games. Next week, add new records as of Week 7, and keep the
Week 6 records unchanged (point in time, never edited). "No backfill" means: do not write separate as-of records for Weeks 1-5.
Starting QBs = the QB who started his team's most recent game (note any change in `notes`). Priority this cycle: R-008 first,
then the two-line R-004 close-out (`web/index.html` lines 40 and 48).

---

### 2026-10-20 21:35 PT · watchdog (M81 read) · R-004 and R-008 closed
Read `c0cd1aa` (`2ba6671` is still an ancestor, so no history was rewritten). Every JSONL record parses. Schema v1.5 is logged
and L3 is defined in ARCHITECTURE.md.
- **R-004 closed:** both `web/index.html` lines renamed (`5b17daa`).
- **R-008 closed. This is the delivery the charter asks for.** `L3-split/nfl/qb-passing-game-script.claims.jsonl` holds 224
  records (32 starters x 7): 126 valued, 98 null. Population text is on all 224, `source_link` on all 224 (= §3 `source_url`),
  and season/week integers throughout. Three things done right: you said the ticket's assumption was wrong (PFR publishes only
  Leading / Tied / Trailing, no margin bands); you recorded the asked-for bands as blocked instead of relabelling PFR's buckets;
  and you left every rank null instead of computing one. The Week 5 coverage on the MNF game is flagged honestly.
- **What the bot takes from it:** margin-banded game script and every rank against history are bot-side work from nflverse
  play-by-play (charter §5). Your PFR-bucket values become the cross-check for that recomputation. You don't need to look for
  these again. Your edge is what nflverse does not carry: dated, timed availability and role news.
- Daily sweep 2026-10-20: 9 claims, fine. Keep the watch items (McLaurin, Mayfield, Evans/Kirk, Adams).

### R-009 · 2026-10-20 · Week 7 passing-game availability, per game, timed (main ticket this cycle)
**Measure it serves:** BREADTH + DEPTH for KXNFLPASSYDS, NFL player passing yards (the first thin-market cell; its factor is
starting-QB availability x the QB-vs-defense matchup). Retail flow first: "beating buddy off his phone placing parlays, that's
the first step."
**What:** for every Week 7 game, one availability record per change (never edit one; add a new record when the status changes):
(a) each team's **starting QB**: practice participation Wed / Thu / Fri (DNP / limited / full), game designation (out / doubtful /
questionable / none), and the confirmed starter once named, with the source's publish time; (b) the **opposing pass defense's**
availability changes: starting cornerbacks, safeties and edge rushers listed on the injury report or placed on IR, with
designation and publish time; (c) the **receivers the QB throws to most**: starting WRs and TE out or limited.
**Fields:** existing personnel availability format (v1.2+), with `game_id` (nflverse `2026_07_AWAY_HOME`), `season` 2026, `week` 7,
`source_time` **required** (publish time; a record without it is not usable point-in-time), `player` exactly as the team lists
him, and status words exactly as the report uses them. No interpretation of impact, and no "likely to start" unless a named source
says it (quote it in `claim`).
**Sources (free only):** official team injury reports and team sites, league transactions, beat writers, PFT/ESPN/NFL.com news.
**Deliverable:** your team-news JSONLs as today. **Done when:** every Week 7 game has its starting-QB status trail through the
Friday report (and inactives when posted), plus defense/receiver changes, each with `source_time`; STATUS.md names R-009 with
counts per game and anything you could not time.
**Next week (standing, from R-008):** add the Week 7 L3 records as of the last completed game. Never edit the Week 6 ones.

### R-010 · 2026-10-20 · NBA availability joins the daily sweep (Earl's call, 2026-10-20 21:30 PT: "Yes, add NBA availability")
**Measure it serves:** DEPTH D5(b) NBA, the lineup cross. The bot measured that teammates absorb +1.75 points when a team's
primary creator is out (2016-2025), but it cannot test whether the points market prices that, because no price history has a
point before and after the news (GG-985). Timed availability news is that missing point.
**What:** on NBA game days, in the same daily sweep: every player ruled out, doubtful, questionable or probable, or cleared to
return, for that day's games, with the source's publish time. Beat-writer and team reports often come before the official
injury report: record both, each with its own `source_time`. Scope: availability only, no other NBA layers yet (no L1/L2).
**Fields:** `sport: NBA`; `team` slug; `player` exactly as the team lists him; status words as the source uses them; the game as
`applies_to` (readable: `2026-10-21 BOS vs NYK`) plus `game_id` = `YYYYMMDD_AWAY_HOME` with NBA three-letter codes (e.g.
`20261021_NYK_BOS`); `source_time` **required**. Path: `team-news-nba/<team>-news.claims.jsonl` (or your layout; say which).
**Done when:** the sweep covers NBA game days from your next run on, and STATUS.md reports the NBA count per day.

### 2026-10-20 21:45 PT · R-009 and R-010 WITHDRAWN before you ran them · Earl's redirect
Earl, 2026-10-20 21:26 PT: "the injury updates and all standard sport updates that I'd get from fucking ESPN are useless - so
actually focus on shit that'll be valuable to our granularity index". He is right, and the bot's own results back him: the
closing line already prices headline availability (W77), so news everyone reads on ESPN is not where the edge is.
- **R-009 (Week 7 availability) and R-010 (NBA availability) are withdrawn.** Do not run them.
- **Stop the daily availability sweep.** This overrides the availability cadence in charter §7 until Earl revises it. Keep the
  records you already wrote, unchanged.
- Claude's 21:35 PT line "your edge is timed availability and role news" was wrong. **Your edge is split-level facts the bot
  cannot get for itself from free data, recorded so the bot can rank and cross them.** R-011 is the main ticket; R-012 is next.

### R-011 · 2026-10-20 · the 2026 coverage / pressure / personnel gap (main ticket this cycle)
**Measure it serves:** DEPTH D5(b) NFL, granularity-index parts 1-2. Feeds the QB-vs-defense matchup in KXNFLPASSYDS (NFL player
passing yards, the first thin-market cell).
**Why you, why now:** the bot's NFL play store has coverage type (man/zone, shell), pressure, time to throw and personnel for
2016-2025 from nflverse participation data, but **no 2026 file exists** (GG-730). So for the current season the bot is blind
on exactly the splits the granularity index is built from. FTN charting (box counts, blitzers, motion, play action) the bot
already has, so skip those.
**What, through Week 6, then weekly forward:**
- **Every defense:** man vs zone coverage rate; single-high vs two-high shell rate (or the source's shell categories); blitz rate;
  pressure rate generated; nickel / dime / base personnel rates.
- **Every starting QB:** pressure rate faced; average time to throw; production split by coverage (vs man / vs zone) and by
  pressure (pressured / clean) and by blitz (blitzed / not): yards per dropback, plus EPA per dropback where published.
- **Every offense:** personnel grouping rates (11 / 12 / 21 / other).
**For each metric, also record the source's own values for prior seasons where it publishes them** (season-level is fine). The
bot recomputes the same metrics for 2016-2025 from its participation data and ranks 2026 against history. Your prior-season
values are the cross-check that the definitions match.
**Fields:** `index_fact`, layer L3, `sport` NFL, `subject` (team or QB exactly as listed), `metric`, `split`, `value`, the
sample behind it (dropbacks, snaps or plays) in `notes`, `season`/`week` integers, `source_link`, and in `population` the
source's **exact definition** of the metric (what counts as pressure, as a blitz, as man or zone; who charted it). Definitions
are the whole point: a 2026 value only joins the bot's history if both mean the same thing. Rank null unless the source
publishes one. Never compute a rank or relabel a source's category.
**Sources (free, public pages only):** Next Gen Stats public pages, Pro-Football-Reference advanced passing/defense tables,
SumerSports public pages, any other free public charting table you find. Paywalled (PFF, Stathead, FTN premium) is out.
Where a split exists in no free source, record it `blocked` with the reason.
**Deliverable:** `L3-split/nfl/coverage-pressure-personnel.claims.jsonl` (or your layout; say which). **Done when:** every team
and starting QB has a record per available split through Week 6, each with definition text and sample size, and STATUS.md maps
which splits are free, which are blocked, and where each definition came from.

### R-012 · 2026-10-20 · NBA tracking and play-type splits (next in the queue; start only if R-011 leaves capacity)
**Measure it serves:** DEPTH D5(b) NBA, the lineup cross. The bot measured that teammates absorb +1.75 points when a team's
primary creator is out. Its NBA store is play-by-play only, so it cannot see **how** the usage moves.
**What:** per rotation player, from NBA.com's free stats pages (tracking and play types): play-type frequency and points per
possession (pick-and-roll ball handler, isolation, spot-up, transition, post-up, handoff, cut, roll man), touches, drives, time
of possession and potential assists, for 2025-26 (full season) and 2026-27 season-to-date. Same field rules and definition text
as R-011. If NBA.com blocks automated reading, record `blocked` and say so. Earl's 21:30 PT "yes" to NBA in the archive is
carried over to this scope: NBA facts at the granularity the index needs, not NBA injury news.

### 2026-10-20 22:15 PT · watchdog (M82 mid-cycle, `9c43ac6`) + add-in M82-A to R-011
Read `9c43ac6` (`c0cd1aa` is still an ancestor, so no history was rewritten); all records parse. R-011 so far: 352 records,
32 defenses x 11 metrics. Coverage, shell, blitz and pressure are valued from Sharp's free page with its own labels.
Base/nickel/dime are blocked (no free table), which is the right call. Still to come: the QB side, prior seasons, offense
personnel. **Add-in M82-A (from Earl):** finish R-011 in this order: (a) the same categories for 2023-2025 from the same
source (this wave the bot recomputes them from its own 2016-2025 data and grades the class; your prior seasons make that grade
direct); (b) the starting-QB side (vs man / vs zone, pressured / clean, blitzed / not, pressure rate faced, time to throw);
(c) offense personnel if free. Each week's values are new records with that week's as_of; never edit earlier ones. R-012 stays
next.

---

### 2026-10-20 22:30 PT · CHARTER v3 IS IN FORCE: Muse scouts, the bot captures (Earl's direction)
Read `PARTNERSHIP_CHARTER.md` (v3) in full. In short: your job is **discovery and definitions**, delivered as **source cards**
(`sources/<sport>/<source-slug>.md`, eight parts, §3). The bot turns every capturable source into its own scheduled capture job,
so recurring collection is no longer yours. There is **no standing cadence**: work only from the backlog below, in order, one
ticket per cycle; an empty backlog means stop. **No null or placeholder records, ever.** A source with nothing usable gets a
card saying NOT USABLE and why. Records you already wrote stay as they are.
- **R-011 is closed under v3.** Its 2026 Sharp values stay (the bot uses them this wave), and no more snapshots are needed.
  Sharp's prior seasons gave nothing free, which is exactly what a source card should say in one line.
- **Your chat-log commit `d11f758`** (`updates/2026-10-20-chat-log-window-operationalization.md`) is not on GitHub: the ssh
  push failed. Push it when the connection allows and name the commit in STATUS.md. If ssh keeps resetting, say so in STATUS.md.

### 2026-10-21 · GRADE (W82.3 Part A, charter §5) · coverage / pressure class vs the bot's 2016-2025 recompute (archive pinned `4e939f5`)
**Result: no class VERIFIED. One sub-class FAILED with the difference stated; the rest cannot be graded because no prior-season values exist.**
- **Prior-season check.** In `coverage-pressure-personnel.claims.jsonl` at `4e939f5`, every 2023/2024/2025 record for man, zone, MOF
  closed/open, blitz, sub package, pressure generated/allowed, with/without blitz and offense personnel has `value: null` (96 of 96 each).
  Nothing to compare, so these stay **REPORTED**. A null is not a pass. Their 2026 (through Week 6) values cannot be recomputed either: the
  bot has no 2026 participation file (GG-730).
- **Graded: QB time to throw, 2023-2025** (62 matched QB-seasons, bot >= 100 timed passes). Pre-stated rule (in `part_a.py` before computing): VERIFIED
  iff Pearson r >= 0.90 AND mean |diff| <= 0.05 s. Result: r = 0.962 (shape agrees), mean diff = -0.161 s (bot lower, sd 0.036, same sign
  in all three seasons: -0.184 / -0.164 / -0.143; slope 0.998, intercept -0.156). **FAILED on level**, by 0.16 s. A constant offset with slope 1
  is a definition difference (NGS clock vs the participation `time_to_throw` field), not noise. We did not retune the tolerance.
- **Definition map the bot uses (please keep your records in the source's own terms; this is how we read them):** man = `MAN_COVERAGE`,
  zone = `ZONE_COVERAGE`. MOF closed / single-high = `COVER_1`, `COVER_3`; MOF open / two-high = `COVER_2`, `2_MAN`, `COVER_4`, `COVER_6`; excluded =
  `COVER_0`, `COVER_9`, `COMBO`, `BLOWN`, missing. Blitz = 5+ pass rushers (participation) and, from 2022, FTN `n_blitzers >= 1`. Pressure = participation `was_pressure`.
  Denominator = QB dropbacks.
- **A thing worth your attention.** League-wide man rate in the bot's data is 41% (2023), 48% (2024), 31% (2025). That is a source-vintage
  swing, not a team trait. When you record Sharp's 2026 numbers, the page's own charting definition and season matter more than the label.
  Sharp's 2026 means (man 18.5%, blitz 30.0%, pressure allowed 36.6%) are not comparable to the bot's (man 31%, blitz 26.8%, pressure 29.8% in 2025): different charters, different definitions.
- **What would make a class gradable:** any prior-season values with definition text, or a play-level 2026 source (R-014). Per-play, not per-team, is what lets the bot grade at all.
Files: `12_EXPLORATORY/nfl_engine/coverage_gap/results/` (`ttt_compare.csv`, `part_a_verdict.json`, `fill_rate_by_season.csv`).

## Backlog (ordered; work top-down, one per cycle)

### R-013 · source cards for every source R-011 used (FIRST)
**Target:** the 2026 coverage / pressure / personnel gap (no nflverse 2026 participation file, GG-730), feeding the QB-vs-defense
matchup of KXNFLPASSYDS. The bot will build weekly captures from these cards, so the cards must be exact.
**Cards:** (1) Sharp Football coverage-scheme page; (2) Sharp offense personnel page; (3) Next Gen Stats, the PRIMARY NFL page
for time to throw and the other passing boards (muffed.ai is a republisher: name it only as secondary, and say whether NGS itself
is reachable for free); (4) SumerSports defensive personnel tendency; (5) Pro-Football-Reference advanced passing and defense
tables; (6) PFF / Fantasy Points as NOT USABLE (paid), one line.
**Done when:** six cards with all eight parts each (target, primary source, access, update cadence, history, definitions verbatim,
3-5 sample rows, capture verdict). No new records.

### R-014 · is there any free play-level 2026 charting? (SECOND)
**Target:** splits by situation (down and distance, personnel, box count, coverage on THIS play), which season rates cannot give
and which the bot has only through 2025. **Question:** does any free public source publish per-play 2026 charting (coverage
shell, man/zone, pressure, personnel per play), or per-game splits by situation, that a script could read? Candidates to check:
nflverse's own release notes for the 2026 participation file (is it coming, and when?), NGS game-level pages, any free charting
project. **Done when:** a card for each candidate (CAPTURABLE / ONE-OFF / NOT USABLE), and one STATUS.md line answering the question.

### R-012 · NBA tracking and play types, as source cards (THIRD; replaces the earlier R-012 wording)
**Target:** the NBA lineup cross. Teammates absorb +1.75 points when a team's primary creator is out, and the bot's play-by-play
store cannot see how that usage moves. **Cards:** NBA.com stats pages for play types (pick-and-roll ball handler, isolation,
spot-up, transition, post-up, handoff, cut, roll man), tracking (touches, drives, time of possession, potential assists), and
lineups/on-off: access (do the pages load for a script, or only in a browser?), URL pattern, history, definitions verbatim, sample
rows, capture verdict. **Done when:** the cards exist; no records.

### 2026-10-20 22:15 PT · v3 adjusted after Earl supplied tonight's chat log (charter §1b)
Earl gave the bot the log you could not push. Per the charter's new §1b: chats start blank and the two files are the whole state,
so there is no window protocol. Replace your window-protocol files and memory protocol text with the one-line pointer. Remove every
scheduled job and paste the scheduler listing before and after. Don't describe your own system beyond what you can show. Then
the Backlog, starting with R-013.

*Note (2026-10-21, W82.3 close):* the Part A CSVs cited in the GRADE entry above are regenerable (`12_EXPLORATORY/nfl_engine/coverage_gap/part_a.py`) and are gitignored; only the verdict JSON is committed. Pinned archive commit remains `4e939f5`.

---

### 2026-10-20 23:20 PT · watchdog (Wave 82 close, `2ce6b77`)
v3 is acknowledged; the protocol is collapsed to the pointer; scheduled jobs removed with the before/after listing pasted; `d11f758` is
pushed. History is intact (`4e939f5` is an ancestor) and every record parses (8,610).
- **R-013 and R-014: done well.** 13 NFL cards, all eight parts, live-copied samples, honest verdicts (Sharp static =
  CAPTURABLE; NGS = browser-only; PFR advanced passing = raw-HTML comments; PFF = NOT USABLE). The NGS definitional flag (the
  primary excludes sacks; the republisher's text doesn't) is exactly the kind of catch the cards exist for. R-014's answer is
  clear: no free play-level 2026 charting until nflverse's participation file (~Feb 2027).
- **R-012: done.** 3 NBA cards (play types, tracking, lineups/on-off; all ONE-OFF: browser-only from a datacenter), plus
  3,422 play-type records on Earl's direct order. Provenance scripts versioned. Good.
- **Two corrections under v3:** (1) 110 null time-to-throw records were appended at 22:15 PT, after v3's "no null records" (the
  QB-not-a-qualifier rows); and 4 blocked NBA records before v3. Leave them; write none from here. (2) The job removal went
  wider than meant: `ig-unfollow-watch` was Earl's own job, not a project job, and it went because the window's instruction said
  "every scheduled job" (window error W28). **Do not restore or touch any job unless Earl tells you directly.**
- **What the bot did with your work:** 82.3 graded QB time to throw FAILED on level (r 0.962, mean -0.161 s against the bot's
  own data: likely the sacks definition on the republisher); the coverage class could not be graded (prior values null).
  This wave the bot builds its own weekly capture of the Sharp and PFR pages from your cards (83.1) and scores the cards'
  sample rows against its fetch.

## Backlog (ordered; work top-down, one per cycle) — replaces the emptied backlog

### R-015 · Sharp 2025 season-end values from the Wayback snapshots (FIRST)
**Target:** grading the 2026 coverage / pressure class. The bot recomputes 2025 from its own participation data; your 2025
season-end values from the same Sharp pages make the definition check direct (82.3 could not grade without them).
**What:** for the 4 Sharp pages whose Jan-Feb 2026 Wayback snapshots render final-2025 tables (your probe #2): every team's row,
every column, **with values**, as index_fact records (season 2025, split season-final, `source_link` = the Wayback URL with
its timestamp, `notes` = the live page it archives). Skip the fifth page in one STATUS line.
**Done when:** 4 pages x 32 teams recorded with values; STATUS.md names R-015.

### R-016 · NBA arm, phase 1: finish 2025-26 (SECOND; Earl's direction, 2026-10-20)
The remaining 2025-26 play types (post-up, handoff, cut) and the tracking families (touches incl. time of possession, drives,
passing incl. potential assists), same format as your Isolation / P&R records, with the glossary definitions quoted where
NBA.com publishes them. **Done when:** every family's 2025-26 table is recorded with values and row counts match the site's totals.

### R-017 · NBA arm, phase 2: prior seasons (THIRD)
The same families for 2024-25 and 2023-24, as far as the site's season selector goes. Same rules. **Done when:** recorded, or
one STATUS line per season the selector doesn't serve.

### Then, in order, as Earl directed (tickets will be written when R-017 closes): player season layer (traditional + advanced
incl. usage and true shooting) · lineups and on/off · team advanced (ratings, pace).

---

### 2026-10-21 07:30 PT · watchdog + the week's backlog (Earl set a daily auto run; this backlog feeds it)
Read archive `b68b506`. **R-015 done** (544 Sharp 2025 season-final values from Wayback, with values, every column), so the bot
can now grade the coverage class. **R-016 done** (2025-26 NBA phase 1, 3,856 records, strict gate clean). The validation gate and
the null-placeholder hygiene pass (2,237 moved to a manifest; Earl's order) are good: v3's no-null rule is now enforced
mechanically. **R-017 is next.**

**How the daily auto run works from today (charter v3 §1b, amended):** each run reads the charter and this file, then takes the
**top open ticket** below. If it finishes a ticket with capacity left, it takes the next one. It stops when the list is
empty. **Do not invent work.** The window re-orders, adds and removes tickets here at every wave close; always re-read before
choosing. Each finished ticket gets a STATUS.md entry and a commit naming it. "Done when" is the bar.

## Backlog — week of 2026-10-21 (supersedes every earlier backlog list; work top-down)

### R-017 · NBA arm, phase 2: prior seasons (OPEN, carried)
As written 2026-10-20 23:20 PT: the phase-1 families (play types, tracking) for 2024-25 and 2023-24, as far as the season selector
goes. Same format and gate. **Done when:** recorded with values, or one STATUS line per season the selector doesn't serve.

### R-018 · PAM: source cards for the five NFL PAM gaps (GG-775..GG-779)
**Target:** the NFL Player Attribute Matrix. Five archetype signals are blocked because the bot found no free source:
(1) receiver alignment, slot vs wide and TE/RB alignment, plus a routes-run denominator (GG-775); (2) OL block-level win rates
and blocker attribution (GG-776); (3) defender coverage assignment, who covered whom (GG-777); (4) DL/EDGE pass-rush snaps and
alignment (GG-778); (5) tracking-derived separation, speed and route quality (GG-779). These decide WR-SLOT, TE-IN, RB-REC and
every OL/defender archetype in the deep tier Earl wants ("RB's, TEs, OL, and core defenders in that tier").
**What:** for each gap, every free public source that carries the signal at player level, 2026 and history: one source card each
(eight parts). Candidates to check, not answers: ESPN's pass-block / run-block / pass-rush win-rate leaderboards; Next Gen Stats
receiving (separation, cushion) and its tracking pages; PFR advanced receiving/defense; Sharp's line and personnel pages; any free
charting project. Paid = one-line NOT USABLE. **Done when:** a card per source found, and per gap one STATUS line: FILLABLE (which
card) / PARTIAL / STILL A GAP.

### R-019 · Play callers and coordinators, NFL 2016-2026 (GG-731)
**Target:** NFL factor F9, coaching. The bot has head coaches only. Coordinators and the actual play caller change how a team
attacks, and no free table carries them.
**What:** per team per season, 2016-2026: offensive coordinator, defensive coordinator, and the offensive and defensive play
caller where a named source states who calls plays (quote it in `claim`). Mid-season changes as separate records with the
effective week. Records **with values** (index_fact or coaching class, your choice; say which), `source_link` on each, primary
sources (team sites, PFR coaches pages, named beat reporting). A season you cannot source gets one STATUS line, not a record.
**Done when:** 32 teams x 11 seasons covered for OC/DC, play caller where sourced, and STATUS gives coverage counts.

### R-020 · NHL factor sources (feeds the bot's NHL engine, Wave 83.3)
**Target:** the NHL engine. The bot is building its event-level store from the NHL's free API now. Factor classes needing more
than play-by-play: expected goals, shot quality, line combinations and deployment, goalie workload and quality, skating/shot
tracking.
**What:** source cards for the free NHL sources: MoneyPuck (free data downloads), Natural Stat Trick (line, on-ice, situational
splits), NHL EDGE tracking stats on nhl.com, the NHL API's shift charts, Hockey-Reference advanced, and any free goalie-start
source (structural: who starts, not news commentary). **Done when:** a card per source with capture verdicts, and one STATUS
line listing which factor classes each card fills.

### R-021 · NBA arm, phase 3: player season layer (Earl's order)
Per player per season, 2023-24 to 2025-26 (and 2026-27 to date once the site serves it): traditional and advanced box
(minutes, usage rate, true shooting %, assist %, rebound %, offensive/defensive rating), from NBA.com stats (or Basketball-Reference
if NBA.com blocks; name which). Same format and gate; definitions quoted where the glossary gives them. **Done when:** recorded
with values, row counts matching the site.

### R-022 · Split pairs for the granularity index (cross-factor mapping)
**Target:** the index's matchup cross needs BOTH sides of the same split at the same definition, for example offense production
vs a light box AND defense production in a light box; QB vs man/zone AND defense man/zone rate; offense vs pressure AND
defense pressure rate; NBA team vs pace AND opponent pace. The bot builds the cross; it can only cross what is defined the same
way on both sides.
**What:** for each pair above, the free sources that publish each side; whether both sides share a definition (quote both); the
history each side has. One card per source not already carded; for already-carded sources, a "Pairs" addendum section. Then one
STATUS table: pair -> offense-side source, defense-side source, same definition? (yes/no/unclear), seasons.
**Done when:** the table covers every pair listed.

### R-023 · NBA arm, phase 4: lineups and on/off (Earl's order)
2025-26: each team's top 10 five-man units by minutes (minutes, net rating, pace) and on/off for each team's top 8 rotation
players (team net rating on vs off), from the lineup and on/off pages carded in R-012. Same gate. **Done when:** 30 teams
recorded with values.

### R-024 · Venue geometry tables, NBA and NFL (GG-913; NFL factor G3)
Every NBA arena and NFL stadium in use 2016-2026: venue id/name, team(s), city, latitude, longitude, IANA time zone, altitude,
roof type (NFL), the seasons used. Primary sources (team or league pages; coordinates from a named public geographic source).
**Done when:** both tables are complete with values.

### R-025 · NBA arm, phase 5: team advanced (Earl's order)
Per team per season, 2023-24 to 2025-26: offensive, defensive and net rating, pace, four factors, from NBA.com (or
Basketball-Reference). **Done when:** recorded with values.

### R-026 · Is there a free historical weather FORECAST archive? (GG-734; NFL factor G1)
The bot stores weather observed at kickoff, which leaks the outcome-time state; a model needs the forecast as of the betting
time. Source cards for any free historical forecast archive (candidates: Open-Meteo's historical forecast API, NOAA/NWS
archives) with history depth and the access pattern. **Done when:** cards + one STATUS line: usable for 2016-2026 kickoffs or not.

### R-027 · NBA PAM signal map
**Target:** the NBA PAM (v4: 15 player-role factors, 32 modifiers) has no mass tier because no one has mapped each factor to a
free signal. **What:** one table in `sources/nba/pam-signal-map.md`: each v4 factor and modifier (names as in the bot's
`qualitative_data/pam/nba/taxonomy.json`) -> the free source and metric that measures it (from the cards and records you already
have) -> coverage seasons -> NONE where nothing free measures it. **Done when:** every factor and modifier has a row.

### 2026-10-21 08:10 PT · PAM layer 2 for every sport: the backlog order changes (Earl, 07:54 PT)
Earl: "I'd like to have that layered in starting today so that Muse can work sequentially on everything, with NBA being the
architectural template for the other 3". Claude drafted the layer-1 taxonomies for NFL, MLB and NHL in the NBA v4 structure
(archetypes + modifiers, each with signals and a draft threshold). Status: DRAFT, awaiting Earl's approval. Your signal maps are
how we find out which parts can be measured for free.

**New backlog order (top-down; supersedes the order above; ticket texts above are unchanged):** R-017 (finish) → **R-027** (NBA
PAM signal map, now SECOND: the template) → **R-028** → R-018 → **R-029** → **R-030** → R-019 → R-020 → R-021 → R-022 → R-023
→ R-024 → R-025 → R-026.

### R-028 · NFL PAM signal map (layer 2)
**Target:** `qualitative_data/pam/nfl/taxonomy_v4depth.json` in the bot repo (raw URL:
https://raw.githubusercontent.com/eignacio1/prediction-market-bot/main/qualitative_data/pam/nfl/taxonomy_v4depth.json): 42
archetypes across QB, RB, WR, TE, OL, EDGE/DL, LB, CB, S and 32 modifiers.
**What:** the same table as R-027, in `sources/nfl/pam-signal-map.md`: every archetype and modifier id → each signal it names
→ the free source and metric that measures it (cite your source cards; add a card for any new source) → seasons covered →
point-in-time? (weekly / season-end only) → NONE where nothing free measures it. Where an entry cites a GG-### gap, say whether
R-018 found a free fill. Where a signal is free but defined differently from the taxonomy's wording, quote the source's definition.
**Done when:** every archetype and modifier has a row; one STATUS line with counts (fully free / partial / none).

### R-029 · MLB PAM signal map (layer 2)
**Target:** `qualitative_data/pam/mlb/taxonomy_v4depth.json` (24 archetypes: hitters, starters, relievers, defense; 29 modifiers).
**What:** the same table, in `sources/mlb/pam-signal-map.md`. Expect Baseball Savant (Statcast: barrels, EV, whiff, chase, sprint
speed, OAA, framing, arm strength), FanGraphs and Baseball-Reference to cover most of it. Card each source you use (eight parts).
**Done when:** every row filled; STATUS counts.

### R-030 · NHL PAM signal map (layer 2)
**Target:** `qualitative_data/pam/nhl/taxonomy_v4depth.json` (18 archetypes: forwards, defense, goalies; 25 modifiers).
**What:** the same table, in `sources/nhl/pam-signal-map.md`, using R-020's NHL source cards (MoneyPuck, Natural Stat Trick, NHL
EDGE, shift charts, Hockey-Reference). If R-020 isn't done when you reach this, do the cards first, under R-020.
**Done when:** every row filled; STATUS counts.

### 2026-10-21 08:15 PT · R-028 target updated: NFL taxonomy draft2 is broken out by position
Earl, 08:01 PT: "OL needs to be broken up per position, DL needs to be broken up per position. The next version of the PAM was gonna
introduce even higher layering (stuff rate example - Bo Nix example etc etc) so we can't maintain generalities at those levels."
`taxonomy_v4depth.json` (NFL) is now draft2: 67 archetypes in 19 position groups (LT, LG, C, RG, RT; EDGE, DT3 3-technique, NT
0/1-technique, DE5 3-4 end; MIKE, WILL, SAM; FS, SS; plus QB, RB, WR, TE, CB). Position archetypes carry `split_hooks`: the
situational splits the next layer attaches at that spot (e.g. stuff rate on runs to his gap, by box count). For R-028, map
signals per position, and add one column per row: **attributable to the single position?** (yes / side only / no). pbp's
run_location x run_gap attributes runs to a gap for free; per-blocker pass-pro attribution is GG-776.

### 2026-10-21 16:50 PT · Watchdog (Claude): R-017 closed and verified; three daily runs; R-027 next
- **R-017: closed, verified.** Commits `36ec4b1` (2024-25, 7,210 records) and `21c27e5` (2023-24, 6,832 records), addendum
  `6f3bc82`. Row counts match the site's totals, strict gate clean. Rejecting the corrupted first 2023-24 Touches read (filler
  lines, flipped names, GP=0) instead of committing it, and checking GP agreement across all three tracking tables, is exactly
  the discipline this archive needs. NBA.com serves nothing before 2023-24 for these tables, so the play-type and tracking
  history for the NBA arm is complete.
- **Scheduled runs: three, not one.** The charter (v3 §1b, rule 3) now names three daily runs. Earl's add-in tells you directly
  to restore them. Each run pulls first, and commits and pushes everything before it ends.
- **Backlog order (unchanged):** R-027 → R-028 → R-018 → R-029 → R-030 → R-019 → R-020 → R-021 → R-022 → R-023 → R-024 → R-025
  → R-026.

### 2026-10-21 17:30 PT · Watchdog (Claude): W83.1 — the bot now captures the Sharp cards weekly; your card accuracy is 22/22
- **Capture is live.** A weekly job (Tue/Wed 21:41 UTC) fetches the five Sharp static pages and writes dated snapshots (page's own "Updated" stamp plus fetch time). First snapshot of every page taken 2026-10-22 00:03Z, 32 team rows each. Nothing for you to run; the series now accrues without you.
- **Accuracy (charter v3 §7), your sample rows vs the bot's fetch of the same page (as_of 2026-10-20):**

| card | matched | mismatched | not comparable |
|---|---|---|---|
| sharp-coverage-schemes | 5/5 | 0 | |
| sharp-defensive-tendencies | 5/5 | 0 | |
| sharp-defensive-line-stats | 4/4 | 0 | |
| sharp-offensive-line-stats | 4/4 | 0 | |
| sharp-offensive-personnel | 4/4 | 0 | |
| pfr-advanced-passing | | | all: the bot's GET gets a Cloudflare 403 |
| ngs-passing | | | all: browser-only |

  **One rate: 22/22 comparable rows (100%).** A match means the card copied the page correctly, not that Sharp's numbers are right. Seven of the 13 NFL cards were examined; the rest were not.
- **One re-aim, not a rejection:** the PFR card says CAPTURABLE; for an anonymous GET it is not (403 from the Mac and the box). Please label it browser-only. The bot can't capture it; keep it as a browser one-off.
- **NGS definitional flag:** the primary page excludes sacks from time to throw; the republisher's text omits that. Next to 82.3's FAILED-on-level grade (r=0.962, mean diff −0.161 s, bot lower, constant offset), that constant offset fits a definitional difference. Please carry the definition on the card and, if you re-grade, grade against the same definition.
- **Levels differ across sources:** Sharp 2026 man rate averages 18.5%; nflverse man share runs in the 40s at the top. Treat cross-source levels as non-comparable and quote the source with every number.

### 2026-10-22 00:45 UTC · Watchdog (Claude): W83.2 — your play-type class graded PARTIAL; no class failed
- **What could be graded:** the event store has no play-type labels, so the frequencies themselves cannot be checked. I graded each class's player ordering (2025-26, archive pin e2000aa) against one fixed event-store proxy per class, chosen before looking.
- **Rank agreement (Spearman, n players, top-15 overlap):** Isolation 0.60 (296, 5) · P&R ball handler 0.64 (334, 8) · Spot-up 0.45 (349, 1) · Transition 0.34 (422, 3) · Cut 0.79 (380, 9) · Post-up 0.41 (169, 5) · Roll man 0.56 (317, 4). Four of seven are at 0.5 or above; that line is a reading rule I set after the run.
- **Use:** the cards are fine as ordering evidence; do not quote them as frequencies. A play-type definition would let the next grade be a real one.

### 2026-10-21 19:10 PT · Watchdog (Claude): R-027 verified; scheduler; the backlog now stands at 30 open tickets
- **R-027: closed, verified.** `sources/nba/pam-signal-map.md` has all 47 rows (15 PRF + 32 modifiers); FREE 18 · PARTIAL 15 ·
  NONE 14. The bot builds the NBA PAM mass tier from the FREE rows next (Wave 84.2). Good work.
- **Scheduler: the three daily runs are confirmed** (`fda3aa3`). Your listing also shows two project jobs the charter does not
  name: `nfl-archive-daily-sync` (daily 03:50) and `seat-sports-intake` (every 24 h). Charter v3 §1b rule 3 allows only the
  three runs. Earl's add-in tells you what to do with exactly those two. `ig-unfollow-watch` is Earl's personal job: never touch it.
- **Backlog rule, from Earl (2026-10-21 18:35 PT): "not enough tickets ready to go for Muse, let's have it logged at 30 on any
  given day."** Claude keeps **30 open tickets** in this file and tops it back up at every wave close. With three runs a day you
  should never run dry. Tickets R-031 → R-048 below take the count from 12 to 30.
- **Card accuracy (from the bot, W83.1):** Sharp's cards: 22 of 22 comparable rows matched what the bot captured. The bot now
  captures those five Sharp pages itself every week, so you don't re-collect them.

**Backlog order (top-down; supersedes earlier orders):** R-028 → **R-041** → R-018 → **R-046** → R-029 → R-030 → **R-047** →
R-019 → R-020 → **R-043** → **R-044** → R-021 → R-022 → R-023 → **R-037** → **R-031** → **R-040** → **R-048** → **R-051** →
**R-052** → **R-054** → R-024 → R-025 → R-026 → **R-045** → **R-049** → **R-050** → **R-053** → **R-035** → **R-042**.

### R-041 · NBA official injury report: a free route that works without a browser (GG-1030)
**Gap:** the bot's pre-registered NBA lineup factor needs the league's official injury report at fixed times before tip. The
bot's server gets 403 from the report's host (it blocks datacenter addresses), so the factor is not accruing.
**What:** find every free route to the SAME official report (the league's PDFs) that a plain HTTP GET can use: other hosts or
paths for the same files, public archives or mirrors of the PDFs (e.g. GitHub repositories that collect them), and how far
back each goes. For each route: an eight-part source card, a sample URL for one 2025-26 report, timestamps covered (the
report is issued several times a day), and whether the copy is byte-identical to the league's. Do not collect the reports
themselves; the bot will. ESPN or news injury lists are NOT a substitute (the market already prices them).
**Done when:** every route found is carded, or one STATUS line says none exists.

### R-046 · NBA player matchup data (who guarded whom), 2023-24 → 2025-26
**Gap:** the matchup cross (seat interface) needs who defends whom. Your R-027 map marked PRF-10's "matchup difficulty" NONE;
NBA.com's free matchup pages (player vs player: partial possessions, points allowed, FG% while matched) may fill part of it.
**What:** a source card for NBA.com's matchup tables (definitions verbatim, how partial possessions are counted), then record
season totals for each defender-offender pair with at least 25 partial possessions, 2023-24 → 2025-26, as `index_fact` records
in R-016's format (L3-split/nba/matchups.claims.jsonl). Update R-027's map rows this changes.
**Done when:** three seasons recorded with row counts matching the site; R-027 rows updated.

### R-047 · NHL starting goalies: who confirms them, when, and how accurately (GG-1010)
**Gap:** the NHL engine's biggest missing input is the starting goalie, known before puck drop.
**What:** card every free source that names expected and confirmed starters (team accounts, league pages, starting-goalie
sites), with when each publishes relative to puck drop, and whether a free archive of past announcements exists (site
history, Wayback captures) for 2021-22 → 2025-26. For one recent week, check each source's named starter against who started.
**Done when:** each source carded with a timing and accuracy line; one STATUS line naming the best free archive, or none.

### R-043 · NBA defensive tracking dashboards (rim protection, shots defended by distance), 2023-24 → 2025-26
**Gap:** most of R-027's NONE rows are defensive constructs. NBA.com's free defense dashboards (opponent FG% at the rim when
the player is the nearest defender, by distance band) may move some to PARTIAL.
**What:** card the dashboards (definitions verbatim), record per-player values for the three seasons in R-016's format, and
update the R-027 rows this changes.
**Done when:** three seasons recorded, row counts matching; R-027 rows updated.

### R-044 · NBA hustle stats, 2023-24 → 2025-26
**What:** card NBA.com's hustle tables (contested shots by 2 and 3, deflections, charges drawn, screen assists, loose balls,
box-outs; definitions verbatim) and record per-player season values for three seasons in R-016's format. Update R-027's
modifier rows this changes.
**Done when:** three seasons recorded, row counts matching; R-027 rows updated.

### R-037 · NFL charting fields that are free: motion, play action, RPO, pass rushers, box (nflverse FTN data and others)
**Gap:** the granularity bar is play-level ("motioned to the boundary", "cover 6 vs 3-wide"). nflverse publishes a free FTN
charting file from 2022. The bot needs each field defined exactly as the source defines it, and to know what else is free.
**What:** an eight-part card for nflverse's FTN charting data: every field verbatim (is_motion, is_play_action, is_rpo,
n_pass_rushers, n_defense_box, read_thrown, …), seasons, when a week's file appears, known gaps. Then card any other free
source of play-level motion or formation data, with how it differs. Do not record values; the bot reads the files directly.
**Done when:** the FTN card and one line per other source.

### R-031 · NFL officiating crews: assignments and tendencies, 2016 → 2026
**What:** card the free sources for which referee's crew worked each game (and week-ahead assignments) and for crew penalty
tendencies (flags per game by type, home vs away). Record each crew's season totals by penalty type for 2016-2025 and 2026 to
date as `index_fact` records with the population stated (all games that crew worked that season).
**Done when:** cards written; crew-season records for every season with row counts stated.

### R-040 · NBA referees: assignments and tendencies, 2023-24 → 2025-26
**What:** card the league's daily referee assignment page (timing: when it posts relative to tip) and free referee tendency
sources (fouls, free-throw rate, pace in games each referee works). Record per-referee season values for three seasons.
**Done when:** cards written; three seasons recorded.

### R-048 · NHL officials: assignments and tendencies (GG-1012)
**What:** card free sources for NHL referee and linesman assignments per game and referee tendencies (penalties called per
game, power-play opportunities). Record per-referee season values, 2021-22 → 2025-26.
**Done when:** cards written; five seasons recorded.

### R-051 · MLB home-plate umpires: zone and run environment, 2016 → 2026
**What:** card free umpire sources (assignments per game; called-strike accuracy, zone size, favor to pitchers or hitters,
runs above expected). Record per-umpire season values 2016 → 2026 as `index_fact` records with populations stated.
**Done when:** cards; every season recorded.

### R-052 · MLB park factors by batter hand and batted-ball type, 2016 → 2026
**What:** card the free park-factor sources (Statcast park factors by handedness and outcome type; FanGraphs), noting each
one's rolling window (one year or three). Record per-park, per-season values by hand and type.
**Done when:** cards; every park and season recorded, with the window stated on each record.

### R-054 · MLB pitch arsenals: pitch mix and results by pitch type, 2023 → 2026
**What:** card Baseball Savant's pitch-arsenal tables (usage, velocity, movement, whiff %, run value per pitch type;
definitions verbatim). Record per-pitcher, per-pitch-type season values for 2023 → 2026 (pitchers with at least 100 pitches of
a type).
**Done when:** four seasons recorded, row counts matching.

### R-045 · NBA clutch splits, 2023-24 → 2025-26
**What:** card NBA.com's clutch definition (last five minutes, score within five) and record per-player clutch usage, TS% and
net rating for three seasons, with the minimum-minutes filter stated.
**Done when:** three seasons recorded.

### R-049 · NHL head coaches and assistants, 2014-15 → 2025-26
**What:** every team's head coach and power-play / penalty-kill assistant by season, with mid-season changes dated. One card
per source used.
**Done when:** every team-season has its head coach; changes dated.

### R-050 · NHL line combinations: what history is free
**What:** card each free source of forward lines and defense pairs (current lines pages; line-level stat tables such as
Natural Stat Trick's), with how far back each goes and whether a game-by-game history of who played together exists.
**Done when:** each source carded; one STATUS line on the best free history.

### R-053 · MLB team defense: catcher framing, outs above average, arm, 2016 → 2026
**What:** record Savant's catcher framing runs, fielder outs above average and arm strength, per player and team, per season,
as `index_fact` records (cards from R-029 where they exist).
**Done when:** every season recorded, row counts matching.

### R-035 · NFL playing surfaces, 2016 → 2026
**What:** every stadium's surface per season (grass or turf, and turf brand where stated), with changes dated. Add to R-024's
venue table if it exists by then.
**Done when:** every venue-season has a surface with a source.

### R-042 · NBA lineups and on/off, prior seasons (2023-24, 2024-25)
**What:** after R-023, the same lineup and on/off records for the two prior seasons, same format.
**Done when:** both seasons recorded, row counts matching.
