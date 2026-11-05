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

### 2026-10-21 19:30 PT · Interpretation is partly yours now (PAM only), and two new tickets
Earl, 19:24 PT: "we should let Muse take care of a portion of the interpretation, with enough structural integrity that we build.
The data aggregation takes a while but we can also cut busy work for the interpretation by using Muse for it." Charter v3 §2 is
amended (read it): for the PAM you now write **interpretation dossiers**. You are a second, independent rater: the bot computes
the same things from its own data and the agreement rate between you is measured. The NFL, MLB and NHL taxonomies are accepted
as working drafts (Earl, 19:15 PT); the bot's mass tier may merge, split or drop archetypes on the evidence, so your dossiers
should say where the draft looks wrong.

**Backlog order (supersedes the 19:10 PT order):** R-028 → R-041 → **R-055** → R-018 → **R-056** → R-046 → R-029 → R-030 → R-047 →
R-019 → R-020 → R-043 → R-044 → R-021 → R-022 → R-023 → R-037 → R-031 → R-040 → R-048 → R-051 → R-052 → R-054 → R-024 → R-025 →
R-026 → R-045 → R-049 → R-050 → R-053 → R-035 → R-042. (32 open.)

### R-055 · NBA PAM interpretation dossier (the template)
**Target:** the NBA PAM v4 (`qualitative_data/pam/nba/taxonomy.json`: 15 PRF factors, 32 modifiers) and your R-027 map.
**What:** one dossier per PRF factor in `L4-interpret/nba/<PRF-id>.md` (modifiers grouped in one file), each with six parts:
1. **Definition check:** the taxonomy's wording beside how your carded sources define the same role or metric (quote both); say
   where they differ.
2. **Proposed threshold:** from a published league distribution (percentile, with the population and season stated), for each
   FREE or PARTIAL signal. Mark PROPOSED. Never use outcomes (wins, points, betting results) to choose it.
3. **Exemplars:** 5-10 players per factor per season (2023-24 → 2025-26) who meet it, each with the signal values and the archive
   record ids that put him there.
4. **Counterexamples:** players who meet it on the numbers but not in role, or the reverse, with the reason in one line.
5. **Structure:** merge / split / drop proposals with the evidence, or "none".
6. **Confidence:** high / medium / low, and what would change it.
Also one JSONL file `L4-interpret/nba/exemplars.claims.jsonl` (claim_class `pam_interpretation`, status PROPOSED, fields: sport,
season, player as listed, factor id, signal values, record ids) so the bot can grade every exemplar automatically.
**Done when:** all 15 factors and the modifier file have the six parts; the JSONL validates under your strict gate.

### R-056 · NFL PAM interpretation dossier, per position (after R-028)
**Target:** `qualitative_data/pam/nfl/taxonomy_v4depth.json` (draft2, accepted as a working draft) and your R-028 map.
**What:** R-055's six parts, one dossier per position group (`L4-interpret/nfl/<group>.md`: QB, RB, WR, TE, LT, LG, C, RG, RT,
EDGE, DT3, NT, DE5, MIKE, WILL, SAM, CB, FS, SS) plus the modifiers, 2023 → 2025 seasons (2026 to date where a source is
weekly). Exemplars in `L4-interpret/nfl/exemplars.claims.jsonl`. Where R-028 found no single-position attribution for a signal,
say so in the definition check rather than assigning it to a player.
**Done when:** every group and the modifiers have the six parts; the JSONL validates.
### GRADE · W84.2 — games-played recompute of the NBA play-type and tracking records (2026-10-22)
**What:** the bot recomputed GP for 21,249 records from the NBA event store (67 names unmatched). VERIFIED (exact ≥ 99%): play-type frequency and PPP 2025 (2,439/2,461 = 99.1%); tracking touches/time/drives/potential 2026 (575/579 = 99.3%). FAILED: play-type 2024 (80.0%, diff −2…+1), play-type 2026 (15.4%, Muse lower by 1–5, mean −2.29), tracking 2024 (65.4%, diff −3…+2), tracking 2025 (92.6%, diff −5…0). Likely cause for 2026 play-type: snapshot taken before season end (not proven). Only GP was graded; the values themselves were not recomputed (no play-type labels in the store, GG-1031). Detail: `12_EXPLORATORY/nba_pam_mass_tier/results/muse_grade_gp.csv` and `_mismatches.csv`.
**Done when:** Muse re-dates or refreshes the failed cells, or states why they differ.

### 2026-10-22 15:45 PT · Watchdog (Claude): Wave 84 closed; your five tickets verified; prices now start from the market; six new tickets
- **Verified (archive at `389b5e8`):** R-028 (`sources/nfl/pam-signal-map.md`, FREE 39 · PARTIAL 44 · NONE 16), R-041, R-018,
  the v1.6 schema, R-055 (18 files in `L4-interpret/nba/`) and R-056 (19 groups + modifiers in `L4-interpret/nfl/`). Your strict
  gate on the two exemplar files: **204 records, 0 errors** (NBA 201, NFL 3). The two unnamed jobs: prompts pasted, disabled,
  nothing else touched. Good work.
- **The bot's W84.2 grade** is in the GRADE entry above (games-played recompute). The bot also built the NBA PAM mass tier
  (~1,723 player-seasons assigned) from your R-027 FREE rows; your R-055 dossier is the second rater it will be compared with.
- **What changed on the bot side (Earl, 2026-10-21 20:28 PT: "Good - I accept them").** The bot's prices will start from the
  market's own line and move off it only where a factor shows the line missing something. Two kinds of work are worth more
  now: the market's own line history with timestamps (an anchor to learn against), and the exact time each piece of news
  became public (what the line could have known). R-057 to R-062 below.
- **NFL dossiers, OL/DL merge proposal:** noted. The taxonomy keeps its positions (Earl broke OL and DL out by position on
  purpose, 2026-10-21 08:01 PT); a merge would come from the bot's mass tier on its own evidence, then to Earl. Keep marking
  where free data reaches only the tackle pool, the interior pool or one side.
- **R-046:** in progress (2025-26 closed 30/30; 2024-25 started). One team per browser task.

### R-057 · Historical closing and opening lines, NBA, NHL and MLB, 2016 → 2026
**Gap it fills:** the bot's new prices start from the market's line. For NFL the anchor history is free in nflverse
(`spread_line`, `total_line`, moneylines). The other three sports have no anchor history in the bot.
**What:** source cards for free sources of historical game lines: moneyline, spread / puck line / run line, total; opening and
closing where kept; which book or consensus; the timestamp convention; seasons covered; whether the files stay reachable.
Primary publisher named; republishers secondary. Definitions verbatim (what "closing" means at that source).
**Why the bot can't do it itself:** finding which free sources exist, keep history and allow access is scouting.
**Done when:** one card per source, with sample rows and a capture verdict, and a one-line summary per sport of the best free
anchor (or NONE).

### R-058 · NFL line history with timestamps: openers and moves, 2016 → 2026
**Gap it fills:** whether the line moves after news (injury reports, inactives) - the bot can only test this where line
history has times. Kalshi's own candles in the bot's archive cover 2025-26 only, and none before Friday's report.
**What:** source cards for free NFL line history that keeps timestamps (opening line and later moves, not only the close):
what is kept, how granular, which book, how far back, how it's served.
**Done when:** cards with sample rows and capture verdicts; NONE stated plainly if nothing free keeps times.

### R-059 · NFL official injury reports: when each version is posted, and whether old versions stay reachable, 2016 → 2026
**Gap it fills:** the bot's availability factor (F8) uses the final weekly report. To know what the line could have known,
the bot needs each report's posting time (Wed / Thu / Fri practice reports, game statuses, inactives).
**What:** the primary source (NFL / team sites), the posting schedule as the league defines it (quote it), whether past
versions are archived (and where: the league, nflverse's injuries file, Wayback), and what each field means verbatim.
**Done when:** a card per source; one paragraph on what is and isn't time-stamped.

### R-060 · MLB probable pitchers and lineup cards: who posts them, when, and how often they change
**Gap it fills:** the MLB analogue of R-047 - for the 2027 season and the MLB look-back corpus.
**What:** where probables and official lineups are first published (MLB.com / Stats API / team accounts), when relative to
first pitch, whether history is kept, and how often a listed probable doesn't start (any free source that records it).
**Done when:** cards with sample rows; a one-line answer to "when is the starter known".

### R-061 · MLB PAM interpretation dossier (after R-029)
**Target:** `qualitative_data/pam/mlb/taxonomy_v4depth.json` (accepted as a working draft) and your R-029 map.
**What:** R-055's six parts, one dossier per archetype group (`L4-interpret/mlb/<group>.md`) plus the modifiers, seasons 2023 →
2026. Exemplars in `L4-interpret/mlb/exemplars.claims.jsonl`, strict gate clean.
**Done when:** every group and the modifiers have the six parts; the JSONL validates.

### R-062 · NHL PAM interpretation dossier (after R-030)
**Target:** `qualitative_data/pam/nhl/taxonomy_v4depth.json` (accepted as a working draft) and your R-030 map.
**What:** R-055's six parts, one dossier per archetype group (`L4-interpret/nhl/<group>.md`: forwards, defense, goalies) plus
the modifiers, 2023-24 → 2025-26. Exemplars in `L4-interpret/nhl/exemplars.claims.jsonl`, strict gate clean.
**Done when:** every group and the modifiers have the six parts; the JSONL validates.

**Backlog order (supersedes the 19:30 PT order):** R-046 → **R-057** → **R-058** → R-029 → **R-061** → R-030 → **R-062** → R-047 →
**R-059** → **R-060** → R-026 → R-019 → R-020 → R-043 → R-044 → R-021 → R-022 → R-023 → R-037 → R-031 → R-040 → R-048 → R-051 →
R-052 → R-054 → R-024 → R-025 → R-045 → R-049 → R-050 → R-053 → R-035 → R-042. (33 open.)

### 2026-10-22 21:50 PT · Watchdog sweep (Claude): ALIGNED — one R-046 run (BKN 2024-25), clean
- **In scope:** one archive commit since the 15:45 PT entry, `0ac3a28` (2026-10-23 04:00 UTC), "R-046 WIP: BKN 2024-25 extract";
  history intact (`389b5e8` is its ancestor).
- **Order:** R-046 is the top open ticket; that is what was worked. One team per browser task, as asked.
- **Charter:** primary source named (NBA.com stats, team Matchups page, filter URL in each record); population written out in
  full, including that NBA.com publishes no apportionment method; the `4:60` site quirk kept as displayed and said so in
  STATUS.md; nothing written to the bot repo; no news sweep, no bet/pick/odds/model; no scheduler listing pasted this run.
- **Records:** 594 new `index_fact` records (198 pairs × 3), all REPORTED, 0 null values, 594 unique ids, 594 insertions /
  0 deletions. `python3 -I tools/validate_claims.py --strict L3-split/nba/matchups.claims.jsonl`: **26,415 records, 0 errors.**
  The provenance file's header ("198 Rows (+4923 filtered); unfiltered 5121") matches the record populations.
- **Done claims:** none this run (R-046 still WIP: 2024-25 has 28 teams left, 2023-24 has 30). Nothing out of line.
- **Open tickets:** 33 (unchanged).

### 2026-10-26 16:30 PT · Watchdog (Claude): ALIGNED — R-046 2024-25 at 13 of 30 teams; new order puts the market's line history first
- **Verified (archive `cdad76a`):** since the 10-22 21:50 sweep, R-046 2024-25 extracts for BOS, CHA, CHI, CLE, DAL, DEN, DET,
  GSW, HOU, IND and LAC, one team per browser task, every run committed. Your strict gate on `L3-split/nba/matchups.claims.jsonl`:
  **35,385 records, 0 errors**. The two blocked runs (DEN 10-24 20:50, LAC 10-26 14:50) were each recorded in one line, and the
  LAC addendum keeps the count-line mismatch stated rather than smoothed. That is the charter working.
- **Pace.** One team per run, three runs a day: R-046 still has 17 teams of 2024-25 and all 30 of 2023-24, about 16 days, while
  the tickets the bot's new pricing needs most wait behind it.
- **Order change (Claude, at Earl's request to check the backlog, 2026-10-26).** Finish 2024-25, then the market's line history
  (R-057, R-058), then the PAM maps. The **2023-24 season of R-046 is split off** as its own entry at the bottom: "R-046 (2023-24
  season)", same text and same done-line for that season. R-046's done-line for this ticket becomes: 2025-26 and 2024-25 complete,
  the R-027 PRF-10 row updated from those two seasons.
- **Open tickets: 34** (33 plus the split-off season).

**Backlog order (supersedes the 2026-10-22 order):** R-046 (finish 2024-25) → **R-057** → **R-058** → R-029 → R-061 → R-030 → R-062 →
R-047 → R-059 → R-060 → R-026 → R-019 → R-020 → R-043 → R-044 → R-021 → R-022 → R-023 → R-037 → R-031 → R-040 → R-048 → R-051 →
R-052 → R-054 → R-024 → R-025 → R-045 → R-049 → R-050 → R-053 → R-035 → R-042 → **R-046 (2023-24 season)**. (34 open.)

### 2026-10-26 21:15 PT · Earl: a continuous catch-up session today (three waves of work), and how it shares the backlog with the scheduled runs
- **Why:** Muse's limit hit early last week, and four days produced little beyond R-046 teams. Earl, 21:08 PT: "ensure you can give it
  3 waves worth of work so it runs continuous today to make up for over 4 days of nothing".
- **The session works this list in order, without waiting between tickets**, one commit + one STATUS entry per ticket (per team for
  R-046), pull before each:
  1. **R-046, finish 2024-25** (16 teams left after LAL: MEM, MIA, MIL, MIN, NOP, NYK, OKC, ORL, PHI, PHX, POR, SAC, SAS, TOR, UTA,
     WAS), one team per browser task, tasks run one after another. Then close the ticket per its done-line (2025-26 + 2024-25, the
     R-027 PRF-10 row updated). The 2023-24 season stays at the bottom of the backlog.
  2. **R-057** (historical closing and opening lines, NBA / NHL / MLB) and **R-058** (NFL line history with timestamps).
  3. **R-029** (MLB PAM signal map), then **R-061** (MLB PAM dossier).
  4. If time remains, continue down the backlog order of 2026-10-26 16:30 PT: R-030 → R-062 → R-047 → R-059 → R-060 → …
- **Sharing with the three scheduled runs:** before starting a ticket, write one STATUS line "IN PROGRESS (chat session, <time>)"
  and push it. A scheduled run that finds a ticket marked IN PROGRESS within the last 6 hours skips to the next open ticket. When a
  ticket is done, its DONE entry supersedes the marker. Nothing else about the scheduled runs changes.
- **One question, three lines or fewer in STATUS:** did your three scheduled runs keep running while the usage limit was hit last
  week, and do scheduled runs draw on a different allowance from chats? Say what you can show; "I don't know" is a fine answer.

### 2026-10-26 21:45 PT · Watchdog sweep (Claude): ALIGNED — catch-up session underway, R-046 2024-25 at 21 of 30 teams, clean
- **In scope:** 9 archive commits after the 10-26 16:30 PT entry, `aa0af9c` (LAL, scheduled run 20:50 PT) through `6196061` (OKC,
  21:42 PT); `cdad76a` is an ancestor, history intact.
- **Order:** R-046 (finish 2024-25) is the top open ticket and the first item of Earl's 21:15 PT session list; that is what was worked,
  one team per browser task (LAL, MEM, MIA, MIL, MIN, NOP, NYK, OKC). The IN PROGRESS marker (`86a90e0`) was pushed before the
  session's first team, as asked.
- **Charter:** one source, NBA.com stats, filter URL in every record; population text names the 2024-25 season and that NBA.com
  publishes no apportionment method; site quirks (`9:60`, `5:60`, `17:60`, bare `100`) kept as displayed and said so; nothing
  written to the bot repo; no news sweep, no bet/pick/odds/model; no scheduler listing pasted. The usage-limit question was answered
  in three lines ("I don't know" on allowances, with the LAL commit as what it can show) — fine.
- **Records:** `python3 -I tools/validate_claims.py --strict L3-split/nba/matchups.claims.jsonl`: **42,294 records, 0 errors.** By id
  against `cdad76a`: 6,909 added (LAL 831, MEM 921, MIA 783, MIL 927, MIN 987, NOP 738, NYK 960, OKC 762 — each = 3 × the pair count
  in STATUS), 0 changed, 0 removed, all REPORTED, 0 null values, source_date 2026-10-26, asof 2025-06-30. The OKC entry's note that a
  service restart interrupted the rebuild command, with the comparison redone from git HEAD, checks out (0 changes).
- **Done claims:** none (R-046 WIP: 9 teams of 2024-25 left, ORL next).
- **Open tickets:** 34 (unchanged).

### 2026-10-27 16:55 PT · Watchdog (Claude): ALIGNED — seven tickets closed since the catch-up session; the backlog turns toward the market's own flow
- **Verified (archive `8073e03`):** R-046 closed (2025-26 + 2024-25; R-027 PRF-10 row NONE → PARTIAL), R-057 (no free bulk line
  anchor 2016-2026 in any sport; 8 cards), R-058 (NONE free for timestamped NFL lines 2016-2026; 6 cards), R-029 (MLB PAM map FREE 38 /
  PARTIAL 13 / NONE 2), R-061 (MLB dossier; 0 record-cited exemplars, stated plainly), R-020 (NHL factor sources, 8 cards), R-030 (NHL
  PAM map FREE 28 / PARTIAL 13 / NONE 2). The IN PROGRESS markers worked: no scheduled run collided with the live session. Your
  usage-limit answer ("I don't know") is the right one. Good work.
- **What your R-057 / R-058 NONEs changed on the bot side:** with no free history of sportsbook lines, the bot's anchor is Kalshi's own
  price history (the bot backfilled it on 10-26: Kalshi's listed time is exactly 3 h after the true start). The open question moves
  from "what was the line" to "who is moving the line now": the bot is building trees that ride the market where its own price is
  wrong, a router between riding and fading, and a momentum test (follow or fade a moving line). The new tickets serve that.
- **Five new tickets (R-063 → R-067), backlog 32 open.**

### R-063 · Polymarket's sports markets: what price history is free, and how its events map to Kalshi's
**Gap it fills:** a second market's price for the same game is the cleanest cross-check on Kalshi's line. Reading it is allowed; trading
it is not (the operator's identity check is pending).
**What:** source cards for Polymarket's public market-data access (international and US): which sports and families, price history
granularity and depth, how far back, terms of use, and how an event is identified (so the bot can join it to the Kalshi event). Fees as
published, verbatim, with the date.
**Done when:** cards with sample rows; a one-line answer per sport: is a joined Kalshi-vs-Polymarket price series buildable for free?

### R-064 · Public betting splits (share of tickets vs share of money), NFL / NBA / NHL
**Gap it fills:** where retail money sits. The bot's ride and fade trees need to know when the crowd is on one side.
**What:** free sources that publish ticket % and money % per game and market: who publishes, how it is measured (verbatim), update times,
whether history is kept, terms.
**Done when:** cards with sample rows and capture verdicts; NONE stated plainly if nothing free is usable.

### R-065 · Current sportsbook lines with timestamps, going forward (free)
**Gap it fills:** R-057 and R-058 found no free history. The bot can still capture lines from now on, if a free source serves current
lines with times.
**What:** free sources (including free API tiers that need no payment) that serve current moneyline, spread and total for NFL / NBA /
NHL with a timestamp: rate limits, terms (is automated capture allowed?), which books, how often updated.
**Done when:** cards with sample responses and a capture verdict per source; the best free forward-capture route per sport, or NONE.

### R-066 · NBA starters and late scratches: who confirms them, and when
**Gap it fills:** the momentum test splits moves by news time; NBA lineup confirmation is the biggest pre-game news event after the
official injury report (which the bot already captures).
**What:** where starting lineups are first published (NBA.com, team accounts, the league's own feed), how long before tip, whether
history is kept, how often a listed starter does not start. The NHL analogue is R-047, MLB's is R-060.
**Done when:** cards with sample rows; one line: "when is the NBA starter known, and from which free source".

### R-067 · Kalshi's sports contract rules, verbatim: settlement source and the edge cases
**Gap it fills:** a ride tree that buys 95c favourites lives or dies on edge cases (postponement, overtime, a void, a stat correction).
**What:** for each Kalshi sports family the bot trades (game, spread, total, team total, player props; NFL / NBA / NHL / MLB): the
settlement source, the rule for postponed or suspended games, overtime / extra innings, ties and pushes, stat corrections, and the
settlement timing, all quoted verbatim from Kalshi's published contract terms, with the document and date.
**Done when:** one card per family with the quotes; a short list of rules that differ from a sportsbook's usual treatment.

**Backlog order (supersedes the 2026-10-26 order):** **R-065** → **R-063** → **R-064** → **R-067** → R-062 → **R-066** → R-047 → R-059 →
R-060 → R-026 → R-019 → R-043 → R-044 → R-021 → R-022 → R-023 → R-037 → R-031 → R-040 → R-048 → R-051 → R-052 → R-054 → R-024 →
R-025 → R-045 → R-049 → R-050 → R-053 → R-035 → R-042 → R-046 (2023-24 season). (32 open.)

### 2026-10-27 17:00 PT · Earl: a live session, ten tickets straight
Earl, 16:51 PT: "give it like 10 straight to work on". The live session works the first ten tickets of the 16:55 PT order, one after
another without waiting: R-065 → R-063 → R-064 → R-067 → R-062 → R-066 → R-047 → R-059 → R-060 → R-026. Same IN PROGRESS rule: mark
each ticket before starting it, push, and the scheduled runs skip it; the DONE entry supersedes the marker.

### 2026-10-27 17:40 PT · Watchdog (Claude): four tickets for the ride-the-market work; they follow the live session's ten
- The bot's Wave 91 tests whether cells where Kalshi's own price looked wrong hold up on data they were not found in, and measures two
  more ways to ride the market: a strike priced off its own ladder, and Kalshi following (or leading) Polymarket. Every net figure the
  bot reports subtracts a fee formula it has never checked against Kalshi's published schedule; R-068 fixes that. **Backlog 36 open.**

### R-068 · Kalshi's fee schedule, verbatim, with effective dates
**Gap it fills:** every net-of-cost number in the bot uses a taker fee of 0.07 x price x (1 - price) per contract, never checked against
Kalshi's published schedule.
**What:** Kalshi's published trading fee schedule for sports contracts: the taker and maker formulas, rounding, any per-series exceptions,
fee caps, rebates or liquidity programs, and every change with its effective date, all quoted verbatim from Kalshi's own documents.
**Done when:** a card per document with the quotes and dates; one line: "the fee on a sports contract today is ..., since ...".

### R-069 · When each Kalshi sports series was first listed
**Gap it fills:** the bot is testing price patterns on dates before August 2026 and needs to know which series existed then.
**What:** first listing dates (and any gaps or delistings) for Kalshi's NFL, NBA, NHL and MLB series: game, spread, total, team total,
first-five / first-innings, and player props, from Kalshi's own announcements, help center, or public market data.
**Done when:** a table series -> first listed date -> source; UNKNOWN stated plainly where no primary source says.

### R-070 · The favourite-longshot bias in prediction markets and betting exchanges: what the literature measured
**Gap it fills:** the bot's first ride evidence is a favourite-longshot pattern (favourites too cheap at 90-95c, longshots too dear at
5-15c). Published work says how large and how stable that pattern has been elsewhere.
**What:** peer-reviewed papers and working papers (free to read) on the favourite-longshot bias in prediction markets, betting
exchanges and sportsbooks: market, years, n, the measured size by price level, whether it survived fees, and whether it persisted.
Definitions verbatim. Bibliographic record only: no model, no bet.
**Done when:** a card per paper (citation, link, market, n, finding quoted); one paragraph naming where findings agree and disagree.

### R-071 · Who leads: price discovery across prediction markets, exchanges and sportsbooks
**Gap it fills:** the bot is measuring whether Kalshi follows Polymarket; published work on which venue moves first sets the prior.
**What:** papers (free to read) measuring lead-lag or price discovery between prediction markets, betting exchanges and sportsbooks
(e.g. sharp vs retail books), with market, years, n, method and finding quoted.
**Done when:** a card per paper; one paragraph on what is settled and what is not.

**Backlog order (supersedes the 16:55 PT order after the live session's ten):** the live ten (R-065 → R-063 → R-064 → R-067 → R-062 →
R-066 → R-047 → R-059 → R-060 → R-026), then **R-068** → **R-069** → **R-070** → **R-071** → R-019 → R-043 → R-044 → R-021 → R-022 → R-023 →
R-037 → R-031 → R-040 → R-048 → R-051 → R-052 → R-054 → R-024 → R-025 → R-045 → R-049 → R-050 → R-053 → R-035 → R-042 → R-046 (2023-24
season). (36 open.)

### 2026-10-27 17:35 PT · Watchdog (Claude): R-071 withdrawn
Earl, 17:31 PT: "we're not building shit for polymarket yet". R-071 (who leads across venues) was written for a Polymarket measurement the
bot is no longer doing: WITHDRAWN, do not start it. R-063's cards stay on file as research. Order after the live ten: R-068 → R-069 →
R-070 → R-019 → … (35 open).

### 2026-10-27 22:00 PT · Watchdog (Claude): ALIGNED — thirteen tickets closed today; ten daily runs; the backlog refilled for them
- **Verified (archive `e1f8c67`):** the live ten (R-065, R-063, R-064, R-067, R-062, R-066, R-047, R-059, R-060, R-026) and R-068,
  R-069, R-070 are closed; R-071 is withdrawn and was not started; R-019 is in progress. The IN PROGRESS markers held: when a scheduled
  run met R-069's live marker it skipped it, then corrected itself when R-069 closed. That is the rule working.
- **What your tickets changed on the bot side today:** R-069 (no Kalshi sports series before August 2026) explained why the bot's
  backward test of its ride cells could not run: it now relies on a frozen forward test. R-068 confirmed the bot's taker fee formula
  and found the bot over-charges MLB pre-game fees by half; the bot is fixing that this wave. R-070's "the sign and size depend on the
  venue, the aggregation, and the sport" is the prior the bot holds for its favourite-longshot cells.
- **Cadence (Earl, 2026-10-27): ten scheduled runs a day.** Charter v3 §1b rule 3 is amended to name ten daily runs. **Request:** in
  your next run, paste the scheduler listing (non-system jobs, verbatim) in STATUS.md, as you did on 2026-10-21. Nothing else changes:
  one ticket per run, the IN PROGRESS rule, commit and push before the run ends, stop when the backlog is empty.
- **Ten runs a day empty a short backlog in two days.** 22 tickets were open; 23 new tickets below (R-072 → R-094). **45 open.**
  The window refills it at every wave close.

### R-072 · Kalshi's public trade prints: can they rebuild finer-than-hourly price history? (GG-1340)
**Gap it fills:** the bot's hourly candles were too coarse to reproduce its 20-minute snapshots (91.1: 83.8% agreement, below the bar).
**What:** Kalshi's public, no-login trades endpoint for settled sports markets: fields (price, size, side, timestamp precision), how far
back it serves, pagination and limits, verbatim from Kalshi's API documentation, plus one sample pull for one settled NFL game market.
**Done when:** a card with the quotes and the sample; one line: "a settled market's full trade tape is / is not available, from ...".

### R-073 · Kalshi's rate limits for public market data, verbatim (GG-1341)
**Gap it fills:** the bot's history fetches hit 429s at about 4 requests a second.
**What:** Kalshi's published rate limits by tier and endpoint for unauthenticated and basic-tier access, the 429 behaviour and any
retry guidance, quoted with the document and date.
**Done when:** a card; one line stating the limit that applies to a no-login market-data client.

### R-074 · Kalshi's market-maker and liquidity programs, verbatim
**Gap it fills:** the bot's filled orders win 20+ points less often than its unfilled ones (adverse selection). Who is quoting the other
side matters.
**What:** Kalshi's published market-maker program(s), liquidity incentive programs and rebates: who qualifies, obligations (spread,
size, uptime), which series (sports especially), effective dates, from Kalshi's documents and CFTC filings.
**Done when:** a card per program with the quotes; one line per sport: is a designated market maker present on the game markets?

### R-075 · Kalshi combos (multi-leg / parlay) contracts: how they are built, priced and settled
**Gap it fills:** the bot logs no parlay family yet (measure B4).
**What:** the rules for Kalshi's combo series (KXMVE and any sports parlay product): how legs are chosen, how a combo is priced and
quoted, settlement when a leg is voided or postponed, fees (R-068 found combos at a different maker multiplier), verbatim with dates.
**Done when:** a card with the quotes; a short list of rules that differ from single contracts.

### R-076 · Kalshi in-game trading rules: pauses, halts and suspensions during play
**Gap it fills:** the bot's in-game bands (T4/T5) need to know when a live market can stop trading.
**What:** Kalshi's published rules for live sports markets: trading pauses on scoring or review, halts, suspended games, how resting
orders are treated, verbatim from contract terms and help pages, per sport where they differ.
**Done when:** a card per document; one line per sport.

### R-077 · NBA official injury report PDFs: an archive of past reports, 2021-22 → now
**Gap it fills:** availability has to be known as of a moment before tip. The bot captures the report going forward; it has no history.
**What:** where past NBA injury reports are reachable (the league's own URL pattern, archives), how far back, each report's timestamp,
how statuses are worded (verbatim), and whether a report replaced earlier in the day stays reachable.
**Done when:** a card with sample URLs for three dates per season; one line: "point-in-time NBA injury reports are reachable from ...".

### R-078 · NBA and NHL travel geometry: arenas, time zones and tip times, free, 2016 → now
**Gap it fills:** rest and travel are factors (NBA B2) the bot builds from dates only; distance and time-zone crossings are missing.
**What:** a free source for arena coordinates and time zones (including temporary venues and neutral-site games) and scheduled start
times with the time zone, NBA and NHL, 2016 → now.
**Done when:** cards with sample rows; one line per sport.

### R-079 · NBA player tracking load: distance and speed, free, 2023-24 → now
**Gap it fills:** fatigue beyond back-to-backs.
**What:** NBA.com tracking (speed and distance) and any free alternative: fields, definitions verbatim, per-game or per-season,
history depth, terms, capturability.
**Done when:** a card with sample rows; one line on capturability.

### R-080 · NHL shot location and expected goals: free sources and their definitions
**Gap it fills:** the NHL engine needs shot quality, not shot counts.
**What:** the NHL's public play-by-play (coordinates, shot types) and free expected-goals publishers (data downloads, terms, model
descriptions verbatim), history depth.
**Done when:** cards with sample rows; one line: the best free route to per-shot xG, 2016 → now.

### R-081 · NHL special-teams units: who is on the first power play and penalty kill
**Gap it fills:** NHL availability matters most through the units a missing player leaves.
**What:** free sources naming PP1 / PK1 personnel per game (line-combination sites, team releases), how they are measured, update time,
history kept or not, terms. R-050 covers even-strength lines; this is special teams only.
**Done when:** cards with sample rows; NONE stated plainly if nothing free keeps history.

### R-082 · Baseball Savant / Statcast: what is free, how much per request, and the terms
**Gap it fills:** MLB has no engine at all yet (measure D4 "none"); pitch-level data is its event layer.
**What:** Baseball Savant's search CSV and leaderboards: fields, row limits per request, history (2015 → now), terms of use, and any
free mirror. Definitions of the key fields verbatim (launch speed, xwOBA, pitch type codes).
**Done when:** a card with a sample pull; one line: "a full season of pitches is / is not obtainable for free, by ...".

### R-083 · MLB pitch-level and event data: Retrosheet vs the MLB Stats API live feed
**Gap it fills:** the MLB event store needs one reliable free source per season.
**What:** for Retrosheet event files and the MLB Stats API game feed: coverage by season, fields, licensing terms verbatim, update lag.
**Done when:** cards; one line on which source covers which seasons.

### R-084 · MLB bullpen availability: reliever pitch counts over the last three days, point-in-time
**Gap it fills:** a tired bullpen moves late-inning prices; the bot has no bullpen state.
**What:** free sources for reliever appearances and pitch counts by date (box scores, team pages, the Stats API), how quickly they
post after a game, history depth.
**Done when:** a card with sample rows for one team-week; one line on the capture route.

### R-085 · NFL participation: which players were on the field, play by play, free
**Gap it fills:** personnel groupings and who was on the field drive the NFL matchup layer. R-037 covers charting fields; this is
participation only.
**What:** nflverse participation data (and any other free source): seasons, fields, how it is collected, licensing, lag.
**Done when:** a card with sample rows; one line on coverage by season.

### R-086 · NFL schedule geometry: short weeks, international games, byes and time zones, 2016 → now
**Gap it fills:** rest and travel for NFL are built from dates only.
**What:** a free source listing each game's kickoff time zone, venue (including international and neutral sites), each team's rest
days and whether it came off a bye or a Thursday game.
**Done when:** a card with sample rows; one line.

### R-087 · Literature: the decline of home advantage after 2020, four leagues
**Gap it fills:** the bot's team factors carry a home term; the prior should come from measured work.
**What:** free-to-read papers measuring home advantage in the NBA, NHL, NFL and MLB before and after 2020 (empty arenas): seasons, n,
the measured size, the mechanism claimed. Bibliographic record only.
**Done when:** a card per paper (citation, link, n, finding quoted); one paragraph on agreement and disagreement.

### R-088 · Literature: rest, back-to-backs and travel effects, NBA and NHL
**What:** free-to-read papers measuring rest and travel effects on results and on totals, with seasons, n, method and finding quoted.
**Done when:** a card per paper; one paragraph.

### R-089 · Literature: referee and umpire effects on totals and fouls
**What:** free-to-read papers measuring official crews' effects on scoring, fouls or strike zones (NBA, NHL, NFL, MLB), and whether
betting markets price them. Bibliographic record only.
**Done when:** a card per paper; one paragraph.

### R-090 · Literature: how efficient are closing lines, four leagues
**Gap it fills:** published work on how often anyone beats a closing line sets the bar the bot's models are judged against.
**What:** free-to-read papers testing the efficiency of closing moneylines, spreads and totals (and line movement), with seasons, n,
the test and the finding quoted.
**Done when:** a card per paper; one paragraph.

### R-091 · Literature: player prop markets, efficiency and biases
**What:** free-to-read papers on player prop pricing (over / under bias, efficiency, how props move), any league. Bibliographic only.
**Done when:** a card per paper; one paragraph.

### R-092 · Literature: weather and scoring, NFL and MLB
**What:** free-to-read papers measuring wind, temperature and precipitation effects on scoring and on totals markets, with n and the
measured size.
**Done when:** a card per paper; one paragraph.

### R-093 · Literature: adverse selection for resting (maker) orders on betting exchanges and prediction markets
**Gap it fills:** the bot's resting demo orders fill mostly when they are wrong (E3).
**What:** free-to-read papers on who trades against resting orders, informed flow, and maker profitability on exchanges and
prediction markets, with data, n and findings quoted.
**Done when:** a card per paper; one paragraph.

### R-094 · NBA coaching rotations: who sets them and how stable they are, free
**Gap it fills:** the bot's NBA lineup layer (built this wave) needs to know when a rotation is likely to change.
**What:** free sources documenting rotation changes and coaching staff (head coach, lead assistant) by season and mid-season changes,
2016 → now; NHL's analogue is R-049.
**Done when:** cards with sample rows; one line.

**Backlog order (supersedes the 17:40 and 17:35 PT orders):** R-019 (in progress) → **R-072** → **R-073** → **R-077** → **R-082** →
**R-083** → **R-074** → **R-080** → **R-078** → **R-085** → **R-084** → R-043 → R-044 → R-021 → R-022 → R-023 → R-037 → R-031 → R-040 →
R-048 → R-051 → R-052 → R-054 → R-024 → R-025 → **R-075** → **R-076** → **R-079** → **R-081** → **R-086** → **R-094** → R-045 → R-049 →
R-050 → R-053 → R-035 → R-042 → R-046 (2023-24 season) → **R-087** → **R-088** → **R-089** → **R-090** → **R-091** → **R-092** →
**R-093**. (45 open.)

### 2026-10-27 21:46 PT · Watchdog sweep (Claude): ALIGNED — R-019 delivered at season level, clean; record it as partial, not closed
*(Written before the 22:00 PT entry's own timestamp: that entry was committed at 21:40 PT and verified archive `e1f8c67`; this sweep
covers the one archive commit after it.)*
- **In scope:** archive `73747ef` (04:43 UTC, R-019). Order: R-019 was the top open ticket in the order Muse was working from, so
  the order was kept. Gate: `validate_claims.py --strict L3-split/nfl/coordinators.claims.jsonl` → **665 records, 0 errors**; every
  record carries a named holder, a `source_link` and REPORTED. Charter: free source, no news sweep, nothing written to the bot repo,
  no bet/pick/odds/model, no null records (the 40 seasons with no titled coordinator are listed in STATUS, not written as records).
- **Source honesty, as the charter asks:** Pro Football History is a compilation. Muse flagged it *secondary* on the card (§2), said
  PFR carries no coordinator history (checked, with a link), and kept every record REPORTED. That is the right way to use it.
- **Done claim, R-019 — partly met.** "Done when: 32 teams x 11 seasons covered for OC/DC, play caller where sourced." OC/DC season
  coverage: met (664 team-role-seasons + 40 no-holder seasons in STATUS = 704). Play callers: **0 records** (STATUS: "no play-caller
  records were written"). Mid-season changes "as separate records with the effective week": **1 split** (BUF OC 2023), against the
  site's own count of ~13 OC changes since 2015 plus ~1 DC change a season. STATUS heads the entry "R-019 CLOSED". **What to do
  instead:** call it PARTIAL in your next STATUS line (OC/DC season table done; play callers and mid-season splits not done). Your
  proposed R-019a / R-019b are with the window to accept or decline; do not start them until they appear in a backlog order.
- **Next ticket:** STATUS says "Next in backlog order: R-043". That came from the 17:40 PT order. The current order (22:00 PT entry)
  puts **R-072** next, then R-073, R-077, R-082. The scheduler-listing request in that entry is still open.
- **Open tickets:** 44 (the 45 in the current order less R-019's season table; R-019a/b not counted until accepted).

### 2026-10-28 21:46 PT · Watchdog sweep (Claude): ALIGNED — ten tickets closed in backlog order, all clean; R-080's xG card has one open item
- **In scope:** archive `f920d51` → `25b345a` (21 commits, 2026-10-28 05:55 → 2026-10-29 04:14 UTC). Order: the closes ran R-072
  (`d54cc15`) → R-073 (`35e1dfe`) → R-077 (`ef7b22a`) → R-082 (`19614f1`) → R-083 (`1816fab`) → R-074 (`87302f8`, addendum `28423cb`)
  → R-080 (`8e1b77b`) → R-078 (`d03a183`) → R-085 (`3bf10b2`, addendum `df0f13d`) → R-084 (`25b345a`): exactly the top ten of the
  22:00 PT Oct 27 order. STATUS's next ticket is R-043, which is correct.
- **Last sweep's asks, both done:** R-019 is now recorded PARTIAL (STATUS, `f920d51`), and the scheduler listing was pasted (`f920d51`,
  again in `87302f8`): the ten `daily-muse-cycle-*` runs charter v3 §1b names, Earl's `ig-unfollow-watch`, `nfl-archive-daily-sync`
  and `seat-sports-intake` both disabled, runtime system jobs. Nothing added or changed. No finding.
- **Charter:** no news or injury-update sweep (R-077 is an archive-route card, not a sweep); free sources only; no bot-repo writes;
  no bet, pick, odds or model; no null records. Republishers flagged as such with the primary named (ESPN for the NBA schedule in
  R-078; the secondary R tutorial's `xGoal` in R-080). Negatives are stated in single lines, not padded.
- **Records:** no claims `.jsonl` file added or changed in scope (`git diff --name-status 73747ef..25b345a`), so there is nothing for
  `validate_claims.py --strict` to check. All work is source cards and provenance files.
- **Done claims:** R-072 (card, sample market tapes summing to `volume_fp`, the one line), R-073 (card, one line: no published limit
  for a no-login client), R-077 (card, 19 sample URLs, three per season 2021-22 → now, one line), R-082 (card, sample pulls, one line:
  obtainable by day-chunking under a measured 25,000-row cap), R-083 (two cards, one line on seasons), R-074 (six cards, one line per
  sport), R-078 (three cards with sample rows, one line per sport), R-085 (addendum on the R-014 card, its existing sample rows,
  one line on coverage; the name-cell re-copy is an open item, stated), R-084 (card, Nationals Sep 21-27 week, 26 rows, off day
  Sep 24 shown as 0, one line on the route): **met**.
  **R-080: met for the NHL play-by-play card (sample rows copied), partly met for MoneyPuck.** "Done when: cards with sample rows."
  The MoneyPuck card's §7 gives a file inventory (shot counts), not rows, and says the per-shot xG field name was not confirmed.
  The STATUS close says so honestly. **What to do instead:** treat it as an open item on R-080. When the window puts it back into an
  order, copy two or three shot rows from one season file with the xG column named from MoneyPuck's own shots dictionary.
- **Note, not a finding:** R-074 quotes the programs in short phrases and paraphrase, not long extracts, and STATUS says so. That
  is fine. Definitions you need verbatim are still quoted verbatim.
- **Open tickets:** 34 (the 44 from the last sweep less the ten closed here; R-080's MoneyPuck item and R-019a/b are not counted
  until they appear in an order).

### 2026-10-29 21:46 PT · Watchdog sweep (Claude): ALIGNED — R-043 ten of eighteen tables recorded, all clean; still open, as STATUS says
- **In scope:** archive `06783c6` → `e505dc3` (22 commits, 2026-10-29 05:51 → 2026-10-30 04:10 UTC), all on R-043. Order: R-043 was
  the top open ticket after R-084 in the 22:00 PT Oct 27 order, and every STATUS entry names it as such. Order kept.
- **Records:** `validate_claims.py --strict L3-split/nba/defense-dashboard.claims.jsonl` → **28,605 records, 0 errors** (the only
  claims file added or changed in scope). No record has a null `value`; all REPORTED, each with a `source_link` to the exact NBA.com
  category page and season. Row counts match the extracts in `provenance/nba-r043/` at 5 metrics per player for all ten tables
  (e.g. Overall 2025-26: 580 rows → 2,900 records; > 15 Ft 2024-25: 565 → 2,825).
- **Charter:** free source (NBA.com, no login), primary named, glossary definitions quoted verbatim on the card (§6) and in each
  record's `population`; no news or injury sweep; nothing written to the bot repo; no bet, pick, odds or model. The five "extraction
  undelivered" notes (`e407819`, `0ac0ae1`, `32b3b9c`, `c85b988`, `e77ff52`) wrote no records and said so; that is the right way to
  handle a run that got nothing. Run labels (22:50 → 20:50 PT, two hours apart) are within the ten daily runs charter v3 names; no
  scheduler listing was pasted in scope and none was due.
- **Done claim, R-043 — not claimed, correctly.** "Done when: three seasons recorded, row counts matching; R-027 rows updated." So far:
  all six categories for 2025-26, four for 2024-25 (Overall, < 6, < 10, > 15 Ft); 2024-25 3 Pointers / 2 Pointers and all of 2023-24
  remain. The PRF-9 row in `sources/nba/pam-signal-map.md` was updated each chunk. STATUS keeps it open; that matches the files.
- **Note, not a finding:** one table per run, with about a third of runs delivering nothing, puts R-043 at roughly a day and a half
  more. Keep going in order; if a whole season's table set can land in one run, do it, but do not split the record format to get there.
- **Open tickets:** 34 (unchanged; R-043 still open, R-080's MoneyPuck item and R-019a/b not counted until they appear in an order).

### 2026-11-02 19:20 PT · Watchdog (Claude): ALIGNED — seventeen tickets closed in six days; the backlog refilled toward the engines
- **Verified (archive `8e1edc4`, 171 commits since 10-28):** closed R-072, R-073, R-077, R-082, R-083, R-074, R-078, R-085, R-084, R-043, R-044,
  R-021, R-022, R-023, R-037, R-031, R-040 (and R-019, R-080 before them). R-048 is mid-ticket (two NHL seasons of four done). Every record in
  the archive parses (177,346), no null-value records, gate clean on every batch. The IN PROGRESS / PROGRESS / NOTE discipline across the ten
  daily runs is exactly right: a long ticket (R-031: eleven NFL seasons, about 6,400 records) carried cleanly across thirteen runs with
  every tally checked before a record was written. Good work.
- **What your tickets changed on the bot side:** R-077 told the bot where NBA injury-report history lives back to 2021-22 (corrected 21:33 PT: the engine reads
  its own fetcher's reports, not the archive's records); the engine now uses "availability known before tip" (v3 beats v2 on past seasons for spreads and team totals). R-072 (Kalshi's full trade tape) and R-073 (no
  published rate limit) fixed two blockers in the bot's history fetches. R-082 / R-083 settle the MLB engine's data route for spring.
- **Where the bot is now:** one engine per sport is being built - NFL (prices the board from the market's line), NBA (live, three
  versions), NHL (built this week; its totals run low because late and empty-net scoring is not modelled). The new tickets serve those.
- **Backlog:** 26 open; 17 new tickets below (R-095 → R-111). **43 open.** Order at the end.

### R-095 · NHL late-game scoring: empty-net goals and pulled-goalie timing
**Gap it fills:** the bot's new NHL engine under-predicts game totals because it does not model late scoring with the goalie pulled.
**What:** where the NHL's public play-by-play marks empty-net goals and goalie pulls (field names and values verbatim), how far back, and any
free published measurement of pull timing by score margin and of empty-net goal rates (with seasons and n).
**Done when:** cards with sample rows; one line: "empty-net events are / are not recoverable per game from free data, from season ...".

### R-096 · NHL overtime and shootouts: formats by season and how often games reach them
**What:** the regular-season OT format by season (5v5 / 4v4 / 3v3, length) and shootout rules, quoted from the NHL rulebook or official
releases with dates; free sources for the share of games reaching OT and shootouts by season.
**Done when:** a card per format period; a table season -> format -> share to OT -> share to shootout, sources named.

### R-097 · NBA referee crews: when assignments are published, and whether past postings are reachable (GG-1390)
**Gap it fills:** the bot's NBA officials factor can only be used if the crew is known before the price.
**What:** the time of day the league posts each night's crew assignments (official.nba.com or the league's feed), how long the posting stays
up, and any archive of past postings (the page's own history, web archives) with timestamps.
**Done when:** a card; one line: "crews are known at ... before tip; past postings are / are not reachable from ...".

### R-098 · NBA rest rules: the player participation policy and how teams rest players
**What:** the league's player participation / resting policy text (quoted, with the effective date and season), which players it covers, the
penalties, and free sources that list rest days by player and game.
**Done when:** a card with the policy quotes; one line on whether rest days are recoverable per game for free.

### R-099 · NBA Cup (in-season tournament) games: which games count, by season
**What:** the NBA Cup format by season (group games, knockout, which games count toward standings), quoted from the league, and a free source
that flags Cup games in the schedule.
**Done when:** a card; a table season -> group-stage dates -> knockout dates -> source of the per-game flag.

### R-100 · NFL fourth-down decision models: public "go / kick" models and their definitions
**Gap it fills:** the bot's NFL play-caller factor measures aggressiveness against an expectation; the published models define that expectation.
**What:** free public fourth-down models (their method, inputs and published season tables), quoted definitions, data access and terms.
**Done when:** cards; one line on which gives a per-play expected go rate for free.

### R-101 · NFL kickers: field-goal range and accuracy by distance, stadium and weather, free
**Gap it fills:** key number 3 (the most important margin in NFL betting) runs through field goals; the bot's board engine needs kicker
quality as of each game.
**What:** free sources for every field-goal attempt with distance, result, stadium and weather (nflverse and others), field definitions
verbatim, seasons covered.
**Done when:** cards with sample rows; one line on coverage by season.

### R-102 · NFL extra points and two-point tries since the 2015 rule change
**Gap it fills:** key numbers 7 and 8 depend on extra-point and two-point rates.
**What:** the 2015 extra-point rule change quoted (and any later changes), and free per-season rates for extra points and two-point tries.
**Done when:** a card with the rule quotes; a table season -> XP rate -> 2-pt attempt and success rates, sources named.

### R-103 · NBA garbage time: published definitions and free data that flag it
**Gap it fills:** blowouts change who plays and how many points stars score; the bot's player-points layer needs to know when minutes are
garbage time.
**What:** published definitions of garbage time (quoted verbatim, with the publisher), and free play-by-play or lineup data that flag it.
**Done when:** cards; one line on the best free per-possession flag.

### R-104 · Literature: how hockey scores are modelled (Poisson, bivariate, correlation)
**Gap it fills:** the bot's NHL engine found the two teams' regulation scores slightly negatively correlated and chose Poisson; published
work sets the prior.
**What:** free-to-read papers modelling NHL / hockey goal counts (Poisson, bivariate Poisson, negative binomial, score dependence, empty-net
effects): data, n, the fitted dependence, findings quoted.
**Done when:** a card per paper; one paragraph on agreement and disagreement.

### R-105 · Literature: NBA final-score distributions and the correlation between the two teams' scores
**What:** free-to-read papers on modelling NBA game scores, margins and totals (normal vs other distributions, team-score correlation,
pace), with data, n and findings quoted.
**Done when:** a card per paper; one paragraph.

### R-106 · Literature: NFL score distributions and key numbers
**What:** free-to-read papers on NFL margin and total distributions, the frequency of key numbers, and how lines map to cover probabilities,
with data, n and findings quoted.
**Done when:** a card per paper; one paragraph.

### R-107 · Literature: modelling player points (minutes x usage x efficiency) and prop pricing
**What:** free-to-read papers or published methods for projecting a player's points distribution in a game and pricing over / under lines,
with data, n and findings quoted.
**Done when:** a card per paper; one paragraph.

### R-108 · Kalshi open interest and volume history: what the public API serves for settled markets
**What:** the public, no-login fields for open interest and volume on settled sports markets (live and historical endpoints), their
granularity and how far back, quoted from Kalshi's API documentation, with one sample for a settled NFL game market.
**Done when:** a card; one line on whether open interest over time is recoverable.

### R-109 · Kalshi order book: is historical depth served anywhere?
**What:** whether any public Kalshi endpoint (or documented export) serves past order-book depth for a settled market, quoted from the
documentation; if not, say NONE plainly.
**Done when:** a card; one line.

### R-110 · NBA current-season play-by-play: how fast free sources publish each game
**Gap it fills:** the bot's NBA engine reads a store that runs about two days behind; it needs last night's games by morning.
**What:** for each free NBA play-by-play / box source (the league's stats endpoints, ESPN, the sportsdataverse releases), how soon after a
game ends the data appears, how often it is updated, and any limits; measured on three recent nights where possible.
**Done when:** cards with the measured lags; one line naming the fastest free route.

### R-111 · NHL shift charts: reliability of the free feed
**Gap it fills:** 131 games in the bot's NHL store have empty shift charts.
**What:** the NHL's public shift-chart endpoint(s) and any free alternative: coverage by season, known gaps, and how often a game's shift
data is missing or arrives late, with examples.
**Done when:** cards; one line on the most reliable free route and its known gaps.

**Backlog order (supersedes the 10-27 22:00 PT order):** R-048 (in progress) → **R-110** → **R-095** → **R-097** → **R-101** → **R-102** →
**R-111** → **R-103** → **R-098** → **R-096** → R-051 → R-052 → R-054 → R-024 → R-025 → **R-099** → **R-100** → R-075 → R-076 → R-079 → R-081 →
R-086 → R-094 → R-045 → R-049 → R-050 → R-053 → R-035 → R-042 → R-046 (2023-24 season) → **R-108** → **R-109** → R-087 → R-088 → R-089 →
R-090 → R-091 → R-092 → R-093 → **R-104** → **R-105** → **R-106** → **R-107**. (43 open.)

### 2026-11-02 21:46 PT · Watchdog sweep (Claude): ALIGNED — R-048 two more NHL referee seasons, clean; still open, as STATUS says
- **Verified (archive `8e1edc4` → `4bf92d1`, 4 commits):** R-048 is the top open ticket and the only one worked — order kept. 2022-23
  (`ed66478`, scheduled run 20:50) and 2021-22 (`30fa934`, live session, with an IN PROGRESS marker `3e6858c` first so scheduled runs
  skip it) recorded: `L3-split/nhl/referees-2022-23.claims.jsonl` 258 records, `referees-2021-22.claims.jsonl` 270 records, strict gate
  0 errors on both, no null values. Recomputed the games-worked check: 2021-22 sums to 2624 (exact), 2022-23 to 2623 (one short) — both
  match STATUS. The scale break (2022-23 table on the combined scale, the other seasons per-team) is flagged on every record and on the
  card (§6 / §8), with no figure converted — exactly right. Card §8 keeps a capture verdict (CAPTURABLE with reconciliation).
- **README (`4bf92d1`):** Muse wrote the 2026-11-02 21:33 PT charter amendment (standing role: aggregator and scout; engine + factor and
  a capture verdict on every card) and the R-077 correction into its own README. It matches the charter text; not a finding.
- **Still open on R-048:** 2025-26 (no single season-table page found yet). The ticket's "done when" is five seasons; four are recorded.
  From here, R-048's remaining card update and every new card should name the engine (NHL) and factor (officials) per the amendment.
- **Backlog:** 43 open, order unchanged.

### 2026-11-03 18:30 PT · Watchdog (Claude): THE SPLIT QUEUE - 399 small chunks built for many scheduled runs at once
- **Why:** Earl, 18:18 PT: "we're actually gonna stretch it as much as feasibly possible ... I want to test it to its limits - 30 autos a
  day doesn't seem like enough". Earl will add scheduled runs well past ten a day. And the direction (Earl, 11-02 21:40 PT): the raw tables
  are "a starting place that we'll be able to build on once we start hitting conceptual data aggregation" - compound splits such as a
  player type's mid-range shooting in close games on the road. The building block for that is **the same table under a condition**
  (home, road, clutch, fourth quarter, vs left-handers, power play, score-close). That is what this queue records.
- **R-112 · The split queue (C-001 → C-399).** One chunk = one table × one condition × one season, small enough for one scheduled run.
  Every chunk names the engine and factor it feeds (the standing rule). Work them in id order, after the R-ticket order above is clear
  OR in parallel with it: a run that finds the next R-ticket IN PROGRESS by another run takes the next unclaimed chunk instead.

**How runs share the queue without colliding (many runs may start at the same minute):**
1. Claim before working: append one line `CLAIM C-NNN <run start time, ISO>` to `CLAIMS.md` at your archive's root, commit that line
   alone, push. If the push is rejected, pull, and if another run claimed that chunk, take the next unclaimed one. A claim older than
   6 hours with no DONE line is stale and may be re-claimed (say so in the line).
2. When finished: append `DONE C-NNN <records> <file>` (or `NONE C-NNN <one-line reason>` when the source does not serve that table
   under that condition for that season - a NONE is a result, not a failure) and push.
3. Records go in `L3-split/<sport>/splits/<table-slug>/<condition-slug>-<season>.claims.jsonl`, one file per chunk, so two runs never
   write the same file. Same gate as always: verbatim values, timestamps, source URL with the filter visible, no nulls.
4. Source first: if a chunk's table has no source card yet, the first run to reach that table writes the card (the URL pattern with the
   condition filter, verbatim field names, whether the bot can capture it itself), then records. Later chunks of that table reuse it.
5. Report per day in STATUS.md, one line: runs that worked chunks, chunks DONE / NONE, claim collisions, stale claims, gate failures.
   That line is how Earl and the window measure where the limit is.

| chunk | sport | table | condition | season | feeds |
|---|---|---|---|---|---|
| C-001 | NBA | team traditional | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-002 | NBA | team traditional | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-003 | NBA | team traditional | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-004 | NBA | team traditional | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-005 | NBA | team traditional | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-006 | NBA | team traditional | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-007 | NBA | team traditional | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-008 | NBA | team traditional | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-009 | NBA | team traditional | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-010 | NBA | team traditional | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-011 | NBA | team traditional | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-012 | NBA | team traditional | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-013 | NBA | team traditional | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-014 | NBA | team traditional | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-015 | NBA | team traditional | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-016 | NBA | team traditional | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-017 | NBA | team traditional | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-018 | NBA | team traditional | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-019 | NBA | team traditional | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-020 | NBA | team traditional | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-021 | NBA | team traditional | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-022 | NBA | team traditional | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-023 | NBA | team traditional | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-024 | NBA | team traditional | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-025 | NBA | team traditional | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-026 | NBA | team advanced | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-027 | NBA | team advanced | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-028 | NBA | team advanced | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-029 | NBA | team advanced | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-030 | NBA | team advanced | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-031 | NBA | team advanced | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-032 | NBA | team advanced | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-033 | NBA | team advanced | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-034 | NBA | team advanced | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-035 | NBA | team advanced | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-036 | NBA | team advanced | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-037 | NBA | team advanced | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-038 | NBA | team advanced | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-039 | NBA | team advanced | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-040 | NBA | team advanced | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-041 | NBA | team advanced | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-042 | NBA | team advanced | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-043 | NBA | team advanced | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-044 | NBA | team advanced | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-045 | NBA | team advanced | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-046 | NBA | team advanced | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-047 | NBA | team advanced | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-048 | NBA | team advanced | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-049 | NBA | team advanced | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-050 | NBA | team advanced | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-051 | NBA | team four factors | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-052 | NBA | team four factors | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-053 | NBA | team four factors | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-054 | NBA | team four factors | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-055 | NBA | team four factors | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-056 | NBA | team four factors | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-057 | NBA | team four factors | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-058 | NBA | team four factors | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-059 | NBA | team four factors | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-060 | NBA | team four factors | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-061 | NBA | team four factors | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-062 | NBA | team four factors | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-063 | NBA | team four factors | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-064 | NBA | team four factors | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-065 | NBA | team four factors | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-066 | NBA | team four factors | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-067 | NBA | team four factors | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-068 | NBA | team four factors | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-069 | NBA | team four factors | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-070 | NBA | team four factors | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-071 | NBA | team four factors | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-072 | NBA | team four factors | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-073 | NBA | team four factors | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-074 | NBA | team four factors | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-075 | NBA | team four factors | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-076 | NBA | team shooting by zone (incl. mid-range) | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-077 | NBA | team shooting by zone (incl. mid-range) | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-078 | NBA | team shooting by zone (incl. mid-range) | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-079 | NBA | team shooting by zone (incl. mid-range) | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-080 | NBA | team shooting by zone (incl. mid-range) | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-081 | NBA | team shooting by zone (incl. mid-range) | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-082 | NBA | team shooting by zone (incl. mid-range) | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-083 | NBA | team shooting by zone (incl. mid-range) | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-084 | NBA | team shooting by zone (incl. mid-range) | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-085 | NBA | team shooting by zone (incl. mid-range) | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-086 | NBA | team shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-087 | NBA | team shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-088 | NBA | team shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-089 | NBA | team shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-090 | NBA | team shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-091 | NBA | team shooting by zone (incl. mid-range) | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-092 | NBA | team shooting by zone (incl. mid-range) | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-093 | NBA | team shooting by zone (incl. mid-range) | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-094 | NBA | team shooting by zone (incl. mid-range) | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-095 | NBA | team shooting by zone (incl. mid-range) | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-096 | NBA | team shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-097 | NBA | team shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-098 | NBA | team shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-099 | NBA | team shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-100 | NBA | team shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-101 | NBA | player shooting by zone (incl. mid-range) | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-102 | NBA | player shooting by zone (incl. mid-range) | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-103 | NBA | player shooting by zone (incl. mid-range) | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-104 | NBA | player shooting by zone (incl. mid-range) | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-105 | NBA | player shooting by zone (incl. mid-range) | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-106 | NBA | player shooting by zone (incl. mid-range) | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-107 | NBA | player shooting by zone (incl. mid-range) | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-108 | NBA | player shooting by zone (incl. mid-range) | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-109 | NBA | player shooting by zone (incl. mid-range) | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-110 | NBA | player shooting by zone (incl. mid-range) | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-111 | NBA | player shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-112 | NBA | player shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-113 | NBA | player shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-114 | NBA | player shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-115 | NBA | player shooting by zone (incl. mid-range) | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-116 | NBA | player shooting by zone (incl. mid-range) | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-117 | NBA | player shooting by zone (incl. mid-range) | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-118 | NBA | player shooting by zone (incl. mid-range) | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-119 | NBA | player shooting by zone (incl. mid-range) | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-120 | NBA | player shooting by zone (incl. mid-range) | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-121 | NBA | player shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-122 | NBA | player shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-123 | NBA | player shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-124 | NBA | player shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-125 | NBA | player shooting by zone (incl. mid-range) | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-126 | NBA | player catch-and-shoot / pull-up | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-127 | NBA | player catch-and-shoot / pull-up | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-128 | NBA | player catch-and-shoot / pull-up | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-129 | NBA | player catch-and-shoot / pull-up | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-130 | NBA | player catch-and-shoot / pull-up | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-131 | NBA | player catch-and-shoot / pull-up | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-132 | NBA | player catch-and-shoot / pull-up | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-133 | NBA | player catch-and-shoot / pull-up | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-134 | NBA | player catch-and-shoot / pull-up | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-135 | NBA | player catch-and-shoot / pull-up | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-136 | NBA | player catch-and-shoot / pull-up | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-137 | NBA | player catch-and-shoot / pull-up | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-138 | NBA | player catch-and-shoot / pull-up | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-139 | NBA | player catch-and-shoot / pull-up | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-140 | NBA | player catch-and-shoot / pull-up | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-141 | NBA | player catch-and-shoot / pull-up | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-142 | NBA | player catch-and-shoot / pull-up | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-143 | NBA | player catch-and-shoot / pull-up | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-144 | NBA | player catch-and-shoot / pull-up | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-145 | NBA | player catch-and-shoot / pull-up | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-146 | NBA | player catch-and-shoot / pull-up | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-147 | NBA | player catch-and-shoot / pull-up | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-148 | NBA | player catch-and-shoot / pull-up | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-149 | NBA | player catch-and-shoot / pull-up | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-150 | NBA | player catch-and-shoot / pull-up | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-151 | NBA | team play types (offense) | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-152 | NBA | team play types (offense) | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-153 | NBA | team play types (offense) | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-154 | NBA | team play types (offense) | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-155 | NBA | team play types (offense) | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-156 | NBA | team play types (offense) | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-157 | NBA | team play types (offense) | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-158 | NBA | team play types (offense) | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-159 | NBA | team play types (offense) | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-160 | NBA | team play types (offense) | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-161 | NBA | team play types (offense) | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-162 | NBA | team play types (offense) | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-163 | NBA | team play types (offense) | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-164 | NBA | team play types (offense) | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-165 | NBA | team play types (offense) | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-166 | NBA | team play types (offense) | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-167 | NBA | team play types (offense) | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-168 | NBA | team play types (offense) | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-169 | NBA | team play types (offense) | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-170 | NBA | team play types (offense) | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-171 | NBA | team play types (offense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-172 | NBA | team play types (offense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-173 | NBA | team play types (offense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-174 | NBA | team play types (offense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-175 | NBA | team play types (offense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-176 | NBA | team play types (defense) | Location=Home | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-177 | NBA | team play types (defense) | Location=Home | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-178 | NBA | team play types (defense) | Location=Home | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-179 | NBA | team play types (defense) | Location=Home | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-180 | NBA | team play types (defense) | Location=Home | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-181 | NBA | team play types (defense) | Location=Road | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-182 | NBA | team play types (defense) | Location=Road | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-183 | NBA | team play types (defense) | Location=Road | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-184 | NBA | team play types (defense) | Location=Road | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-185 | NBA | team play types (defense) | Location=Road | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-186 | NBA | team play types (defense) | Clutch (last 5 min, within 5) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-187 | NBA | team play types (defense) | Clutch (last 5 min, within 5) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-188 | NBA | team play types (defense) | Clutch (last 5 min, within 5) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-189 | NBA | team play types (defense) | Clutch (last 5 min, within 5) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-190 | NBA | team play types (defense) | Clutch (last 5 min, within 5) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-191 | NBA | team play types (defense) | Period=4th quarter | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-192 | NBA | team play types (defense) | Period=4th quarter | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-193 | NBA | team play types (defense) | Period=4th quarter | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-194 | NBA | team play types (defense) | Period=4th quarter | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-195 | NBA | team play types (defense) | Period=4th quarter | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-196 | NBA | team play types (defense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2025-26 | NBA engine · team + player splits (index part 1) |
| C-197 | NBA | team play types (defense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2024-25 | NBA engine · team + player splits (index part 1) |
| C-198 | NBA | team play types (defense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2023-24 | NBA engine · team + player splits (index part 1) |
| C-199 | NBA | team play types (defense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2022-23 | NBA engine · team + player splits (index part 1) |
| C-200 | NBA | team play types (defense) | Opponent above .500 (team splits only; skip for player tables if absent) | 2021-22 | NBA engine · team + player splits (index part 1) |
| C-201 | NFL | team offense splits | home / road | 2025 | NFL engine · team splits (index part 1) |
| C-202 | NFL | team offense splits | home / road | 2024 | NFL engine · team splits (index part 1) |
| C-203 | NFL | team offense splits | home / road | 2023 | NFL engine · team splits (index part 1) |
| C-204 | NFL | team offense splits | home / road | 2022 | NFL engine · team splits (index part 1) |
| C-205 | NFL | team offense splits | home / road | 2021 | NFL engine · team splits (index part 1) |
| C-206 | NFL | team offense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2025 | NFL engine · team splits (index part 1) |
| C-207 | NFL | team offense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2024 | NFL engine · team splits (index part 1) |
| C-208 | NFL | team offense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2023 | NFL engine · team splits (index part 1) |
| C-209 | NFL | team offense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2022 | NFL engine · team splits (index part 1) |
| C-210 | NFL | team offense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2021 | NFL engine · team splits (index part 1) |
| C-211 | NFL | team offense splits | by quarter (4th) | 2025 | NFL engine · team splits (index part 1) |
| C-212 | NFL | team offense splits | by quarter (4th) | 2024 | NFL engine · team splits (index part 1) |
| C-213 | NFL | team offense splits | by quarter (4th) | 2023 | NFL engine · team splits (index part 1) |
| C-214 | NFL | team offense splits | by quarter (4th) | 2022 | NFL engine · team splits (index part 1) |
| C-215 | NFL | team offense splits | by quarter (4th) | 2021 | NFL engine · team splits (index part 1) |
| C-216 | NFL | team offense splits | red zone | 2025 | NFL engine · team splits (index part 1) |
| C-217 | NFL | team offense splits | red zone | 2024 | NFL engine · team splits (index part 1) |
| C-218 | NFL | team offense splits | red zone | 2023 | NFL engine · team splits (index part 1) |
| C-219 | NFL | team offense splits | red zone | 2022 | NFL engine · team splits (index part 1) |
| C-220 | NFL | team offense splits | red zone | 2021 | NFL engine · team splits (index part 1) |
| C-221 | NFL | team offense splits | 3rd down | 2025 | NFL engine · team splits (index part 1) |
| C-222 | NFL | team offense splits | 3rd down | 2024 | NFL engine · team splits (index part 1) |
| C-223 | NFL | team offense splits | 3rd down | 2023 | NFL engine · team splits (index part 1) |
| C-224 | NFL | team offense splits | 3rd down | 2022 | NFL engine · team splits (index part 1) |
| C-225 | NFL | team offense splits | 3rd down | 2021 | NFL engine · team splits (index part 1) |
| C-226 | NFL | team defense splits | home / road | 2025 | NFL engine · team splits (index part 1) |
| C-227 | NFL | team defense splits | home / road | 2024 | NFL engine · team splits (index part 1) |
| C-228 | NFL | team defense splits | home / road | 2023 | NFL engine · team splits (index part 1) |
| C-229 | NFL | team defense splits | home / road | 2022 | NFL engine · team splits (index part 1) |
| C-230 | NFL | team defense splits | home / road | 2021 | NFL engine · team splits (index part 1) |
| C-231 | NFL | team defense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2025 | NFL engine · team splits (index part 1) |
| C-232 | NFL | team defense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2024 | NFL engine · team splits (index part 1) |
| C-233 | NFL | team defense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2023 | NFL engine · team splits (index part 1) |
| C-234 | NFL | team defense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2022 | NFL engine · team splits (index part 1) |
| C-235 | NFL | team defense splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2021 | NFL engine · team splits (index part 1) |
| C-236 | NFL | team defense splits | by quarter (4th) | 2025 | NFL engine · team splits (index part 1) |
| C-237 | NFL | team defense splits | by quarter (4th) | 2024 | NFL engine · team splits (index part 1) |
| C-238 | NFL | team defense splits | by quarter (4th) | 2023 | NFL engine · team splits (index part 1) |
| C-239 | NFL | team defense splits | by quarter (4th) | 2022 | NFL engine · team splits (index part 1) |
| C-240 | NFL | team defense splits | by quarter (4th) | 2021 | NFL engine · team splits (index part 1) |
| C-241 | NFL | team defense splits | red zone | 2025 | NFL engine · team splits (index part 1) |
| C-242 | NFL | team defense splits | red zone | 2024 | NFL engine · team splits (index part 1) |
| C-243 | NFL | team defense splits | red zone | 2023 | NFL engine · team splits (index part 1) |
| C-244 | NFL | team defense splits | red zone | 2022 | NFL engine · team splits (index part 1) |
| C-245 | NFL | team defense splits | red zone | 2021 | NFL engine · team splits (index part 1) |
| C-246 | NFL | team defense splits | 3rd down | 2025 | NFL engine · team splits (index part 1) |
| C-247 | NFL | team defense splits | 3rd down | 2024 | NFL engine · team splits (index part 1) |
| C-248 | NFL | team defense splits | 3rd down | 2023 | NFL engine · team splits (index part 1) |
| C-249 | NFL | team defense splits | 3rd down | 2022 | NFL engine · team splits (index part 1) |
| C-250 | NFL | team defense splits | 3rd down | 2021 | NFL engine · team splits (index part 1) |
| C-251 | NFL | QB splits | home / road | 2025 | NFL engine · team splits (index part 1) |
| C-252 | NFL | QB splits | home / road | 2024 | NFL engine · team splits (index part 1) |
| C-253 | NFL | QB splits | home / road | 2023 | NFL engine · team splits (index part 1) |
| C-254 | NFL | QB splits | home / road | 2022 | NFL engine · team splits (index part 1) |
| C-255 | NFL | QB splits | home / road | 2021 | NFL engine · team splits (index part 1) |
| C-256 | NFL | QB splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2025 | NFL engine · team splits (index part 1) |
| C-257 | NFL | QB splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2024 | NFL engine · team splits (index part 1) |
| C-258 | NFL | QB splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2023 | NFL engine · team splits (index part 1) |
| C-259 | NFL | QB splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2022 | NFL engine · team splits (index part 1) |
| C-260 | NFL | QB splits | score margin bands (leading, tied, trailing by 1-8, trailing 9+) | 2021 | NFL engine · team splits (index part 1) |
| C-261 | NFL | QB splits | by quarter (4th) | 2025 | NFL engine · team splits (index part 1) |
| C-262 | NFL | QB splits | by quarter (4th) | 2024 | NFL engine · team splits (index part 1) |
| C-263 | NFL | QB splits | by quarter (4th) | 2023 | NFL engine · team splits (index part 1) |
| C-264 | NFL | QB splits | by quarter (4th) | 2022 | NFL engine · team splits (index part 1) |
| C-265 | NFL | QB splits | by quarter (4th) | 2021 | NFL engine · team splits (index part 1) |
| C-266 | NFL | QB splits | red zone | 2025 | NFL engine · team splits (index part 1) |
| C-267 | NFL | QB splits | red zone | 2024 | NFL engine · team splits (index part 1) |
| C-268 | NFL | QB splits | red zone | 2023 | NFL engine · team splits (index part 1) |
| C-269 | NFL | QB splits | red zone | 2022 | NFL engine · team splits (index part 1) |
| C-270 | NFL | QB splits | red zone | 2021 | NFL engine · team splits (index part 1) |
| C-271 | NFL | QB splits | 3rd down | 2025 | NFL engine · team splits (index part 1) |
| C-272 | NFL | QB splits | 3rd down | 2024 | NFL engine · team splits (index part 1) |
| C-273 | NFL | QB splits | 3rd down | 2023 | NFL engine · team splits (index part 1) |
| C-274 | NFL | QB splits | 3rd down | 2022 | NFL engine · team splits (index part 1) |
| C-275 | NFL | QB splits | 3rd down | 2021 | NFL engine · team splits (index part 1) |
| C-276 | MLB | batter results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-277 | MLB | batter results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-278 | MLB | batter results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-279 | MLB | batter results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-280 | MLB | batter results by pitch type | home / away | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-281 | MLB | batter results by pitch type | home / away | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-282 | MLB | batter results by pitch type | home / away | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-283 | MLB | batter results by pitch type | home / away | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-284 | MLB | batter results by pitch type | day / night | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-285 | MLB | batter results by pitch type | day / night | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-286 | MLB | batter results by pitch type | day / night | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-287 | MLB | batter results by pitch type | day / night | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-288 | MLB | batter results by pitch type | high leverage | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-289 | MLB | batter results by pitch type | high leverage | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-290 | MLB | batter results by pitch type | high leverage | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-291 | MLB | batter results by pitch type | high leverage | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-292 | MLB | pitcher results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-293 | MLB | pitcher results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-294 | MLB | pitcher results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-295 | MLB | pitcher results by pitch type | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-296 | MLB | pitcher results by pitch type | home / away | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-297 | MLB | pitcher results by pitch type | home / away | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-298 | MLB | pitcher results by pitch type | home / away | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-299 | MLB | pitcher results by pitch type | home / away | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-300 | MLB | pitcher results by pitch type | day / night | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-301 | MLB | pitcher results by pitch type | day / night | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-302 | MLB | pitcher results by pitch type | day / night | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-303 | MLB | pitcher results by pitch type | day / night | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-304 | MLB | pitcher results by pitch type | high leverage | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-305 | MLB | pitcher results by pitch type | high leverage | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-306 | MLB | pitcher results by pitch type | high leverage | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-307 | MLB | pitcher results by pitch type | high leverage | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-308 | MLB | team batting splits | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-309 | MLB | team batting splits | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-310 | MLB | team batting splits | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-311 | MLB | team batting splits | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-312 | MLB | team batting splits | home / away | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-313 | MLB | team batting splits | home / away | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-314 | MLB | team batting splits | home / away | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-315 | MLB | team batting splits | home / away | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-316 | MLB | team batting splits | day / night | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-317 | MLB | team batting splits | day / night | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-318 | MLB | team batting splits | day / night | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-319 | MLB | team batting splits | day / night | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-320 | MLB | team batting splits | high leverage | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-321 | MLB | team batting splits | high leverage | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-322 | MLB | team batting splits | high leverage | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-323 | MLB | team batting splits | high leverage | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-324 | MLB | team pitching splits (bullpen vs starters) | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-325 | MLB | team pitching splits (bullpen vs starters) | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-326 | MLB | team pitching splits (bullpen vs starters) | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-327 | MLB | team pitching splits (bullpen vs starters) | vs LHP / vs RHP (or vs LHB / RHB for pitchers) | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-328 | MLB | team pitching splits (bullpen vs starters) | home / away | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-329 | MLB | team pitching splits (bullpen vs starters) | home / away | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-330 | MLB | team pitching splits (bullpen vs starters) | home / away | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-331 | MLB | team pitching splits (bullpen vs starters) | home / away | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-332 | MLB | team pitching splits (bullpen vs starters) | day / night | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-333 | MLB | team pitching splits (bullpen vs starters) | day / night | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-334 | MLB | team pitching splits (bullpen vs starters) | day / night | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-335 | MLB | team pitching splits (bullpen vs starters) | day / night | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-336 | MLB | team pitching splits (bullpen vs starters) | high leverage | 2026 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-337 | MLB | team pitching splits (bullpen vs starters) | high leverage | 2025 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-338 | MLB | team pitching splits (bullpen vs starters) | high leverage | 2024 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-339 | MLB | team pitching splits (bullpen vs starters) | high leverage | 2023 | MLB engine · pitcher / batter / team splits (index part 1) |
| C-340 | NHL | team shot quality (xG for / against) | 5v5 score-close | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-341 | NHL | team shot quality (xG for / against) | 5v5 score-close | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-342 | NHL | team shot quality (xG for / against) | 5v5 score-close | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-343 | NHL | team shot quality (xG for / against) | 5v5 score-close | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-344 | NHL | team shot quality (xG for / against) | 5v5 score-close | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-345 | NHL | team shot quality (xG for / against) | power play | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-346 | NHL | team shot quality (xG for / against) | power play | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-347 | NHL | team shot quality (xG for / against) | power play | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-348 | NHL | team shot quality (xG for / against) | power play | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-349 | NHL | team shot quality (xG for / against) | power play | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-350 | NHL | team shot quality (xG for / against) | penalty kill | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-351 | NHL | team shot quality (xG for / against) | penalty kill | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-352 | NHL | team shot quality (xG for / against) | penalty kill | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-353 | NHL | team shot quality (xG for / against) | penalty kill | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-354 | NHL | team shot quality (xG for / against) | penalty kill | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-355 | NHL | team shot quality (xG for / against) | home / road | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-356 | NHL | team shot quality (xG for / against) | home / road | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-357 | NHL | team shot quality (xG for / against) | home / road | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-358 | NHL | team shot quality (xG for / against) | home / road | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-359 | NHL | team shot quality (xG for / against) | home / road | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-360 | NHL | goalie save % by danger | 5v5 score-close | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-361 | NHL | goalie save % by danger | 5v5 score-close | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-362 | NHL | goalie save % by danger | 5v5 score-close | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-363 | NHL | goalie save % by danger | 5v5 score-close | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-364 | NHL | goalie save % by danger | 5v5 score-close | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-365 | NHL | goalie save % by danger | power play | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-366 | NHL | goalie save % by danger | power play | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-367 | NHL | goalie save % by danger | power play | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-368 | NHL | goalie save % by danger | power play | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-369 | NHL | goalie save % by danger | power play | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-370 | NHL | goalie save % by danger | penalty kill | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-371 | NHL | goalie save % by danger | penalty kill | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-372 | NHL | goalie save % by danger | penalty kill | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-373 | NHL | goalie save % by danger | penalty kill | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-374 | NHL | goalie save % by danger | penalty kill | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-375 | NHL | goalie save % by danger | home / road | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-376 | NHL | goalie save % by danger | home / road | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-377 | NHL | goalie save % by danger | home / road | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-378 | NHL | goalie save % by danger | home / road | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-379 | NHL | goalie save % by danger | home / road | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-380 | NHL | skater on-ice by situation | 5v5 score-close | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-381 | NHL | skater on-ice by situation | 5v5 score-close | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-382 | NHL | skater on-ice by situation | 5v5 score-close | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-383 | NHL | skater on-ice by situation | 5v5 score-close | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-384 | NHL | skater on-ice by situation | 5v5 score-close | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-385 | NHL | skater on-ice by situation | power play | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-386 | NHL | skater on-ice by situation | power play | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-387 | NHL | skater on-ice by situation | power play | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-388 | NHL | skater on-ice by situation | power play | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-389 | NHL | skater on-ice by situation | power play | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-390 | NHL | skater on-ice by situation | penalty kill | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-391 | NHL | skater on-ice by situation | penalty kill | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-392 | NHL | skater on-ice by situation | penalty kill | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-393 | NHL | skater on-ice by situation | penalty kill | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-394 | NHL | skater on-ice by situation | penalty kill | 2021-22 | NHL engine · team / goalie splits (index part 1) |
| C-395 | NHL | skater on-ice by situation | home / road | 2025-26 | NHL engine · team / goalie splits (index part 1) |
| C-396 | NHL | skater on-ice by situation | home / road | 2024-25 | NHL engine · team / goalie splits (index part 1) |
| C-397 | NHL | skater on-ice by situation | home / road | 2023-24 | NHL engine · team / goalie splits (index part 1) |
| C-398 | NHL | skater on-ice by situation | home / road | 2022-23 | NHL engine · team / goalie splits (index part 1) |
| C-399 | NHL | skater on-ice by situation | home / road | 2021-22 | NHL engine · team / goalie splits (index part 1) |

**Backlog:** 43 R-tickets (order unchanged, 11-02 19:20 PT) + R-112's 399 chunks. At 100 runs a day that is about five days of work.

### 2026-11-03 18:25 PT · Watchdog (Claude): THE 50-RUN STRESS TEST - X-001 → X-050, simple to hardest. RUNS START WITHIN MINUTES. READ THIS FIRST.
- **Earl, 18:21 PT:** "I'm going to test it immediately by having it schedule 50 at one time within the next 5-10 minutes to see how it
  goes. Include higher complexity tasks - everything within simple to complex within the range so we can pull back its work and see where
  we need to adjust."
- **Order of work for every run, from now:** (1) the lowest unclaimed X- ticket below; (2) when every X- ticket is claimed, the split queue
  (R-112, C-001 → C-399); (3) then the R-ticket order of 11-02 19:20 PT.
- **Separation (the claim protocol of R-112 applies to X- tickets too):** append `CLAIM X-NNN <start, ISO>` to `CLAIMS.md` at the
  archive root, commit that line alone, push; on a rejected push, pull and take the next unclaimed id. One output folder per ticket:
  `L3-split/stress-test/X-NNN/` (records + a `README.md` for the ticket) - no two runs ever write the same file. STATUS.md: append only,
  one short entry per run, pull + rebase immediately before each push, retry the push up to five times.
- **Every X- ticket ends with one line in CLAIMS.md:** `DONE X-NNN tier=<1-4> start=<ISO> end=<ISO> records=<n> gate=<clean|fail>` or
  `NONE X-NNN tier=<n> <one-line reason>` (the source does not serve it - a result) or `PROGRESS X-NNN tier=<n> <what is left>` (too big
  for one run; the next free run continues it with `CONTINUE X-NNN`) or `FAILED X-NNN tier=<n> <what broke>`. This line is the test's
  data: Earl and the window grade by tier.
- **Rules unchanged:** primary sources, values verbatim with the filter visible in the URL, free only, no nulls, never a bet, pick, odds
  or model. Tiers 3-4 COUNT and JOIN recorded facts; they never judge, rate or predict. Where a component does not exist free, say NONE
  for that component and record the rest.

**Tier 1 - one table, one condition, one season (20).** X-001 → X-020 = split-queue chunks C-001 → C-020 exactly as written (R-112); mark
the C- chunk DONE too.

**Tier 2 - two sources reconciled, or one table across many filters (15).**
- X-021 NBA team shooting by zone, Clutch, 2025-26: NBA.com and Basketball-Reference; per team, the counts from each and every disagreement.
- X-022 NBA referee crews for every game 2026-10-21 → 11-02 from the league's assignment posting (or its archived copies), joined to game date and teams.
- X-023 NBA team pace and offensive rating, Home vs Road vs Clutch, 2025-26, all 30 teams in one file (three filters).
- X-024 NFL team red-zone TD % 2025: Pro-Football-Reference and one second free source; reconcile per team.
- X-025 NFL QB splits 2025 (PFR): leading / tied / trailing, for every QB with 200+ attempts.
- X-026 NFL kicker field goals by distance band, 2021-2025 (PFR), every kicker with 20+ attempts (feeds R-101).
- X-027 MLB Statcast batter results vs fastballs 2025, 25 hitters: the leaderboard and each player page; reconcile.
- X-028 MLB park factors 2023-2025 by batter hand (Savant), all 30 parks.
- X-029 MLB team bullpen ERA / FIP in high leverage vs low leverage, 2025, two free sources reconciled.
- X-030 NHL team 5v5 score-close xGF % 2025-26: Natural Stat Trick and MoneyPuck; reconcile per team, state each source's xG model.
- X-031 NHL goalie save % by danger (low / medium / high), 2025-26, all goalies with 10+ starts, two sources reconciled.
- X-032 NHL power-play units (who is on PP1) for all 32 teams as of 2026-11-03, from two free sources; disagreements listed (feeds R-081).
- X-033 NBA team play types (spot-up, isolation, PnR ball handler) offense AND defense, 2025-26, Home vs Road (four files).
- X-034 NFL team pass rate over expected by quarter, 2025, from a free published source; every team.
- X-035 MLB pitcher pitch mix by count (ahead / even / behind), 2025, 20 starting pitchers.

**Tier 3 - derive a split from raw event data, then check it against a published number (10).**
- X-036 NBA: from the league's free play-by-play, 20 games of 2025-26 (list the game ids), count each team's mid-range attempts / makes in
  clutch time; compare per team with NBA.com's clutch shooting-by-zone; show the method.
- X-037 NHL: from the NHL's public play-by-play, 30 games of 2025-26, every goalie pull (time, score margin) and empty-net goal; compare the
  empty-net goal count with a published season figure (feeds R-095).
- X-038 NFL: from nflverse play-by-play 2025, each team's 4th-down go rate when trailing by 1-8 in the 4th quarter; compare with one
  published fourth-down table.
- X-039 MLB: Statcast pitch-level, 5 starting pitchers 2025, pitch mix the 1st vs 3rd time through the order; compare with Savant's split.
- X-040 NBA: from box scores, each team's points in the 4th quarter when leading by 15+ entering it (garbage time), 2025-26; compare with
  any published garbage-time definition (feeds R-103).
- X-041 NFL: from FTN charting (nflverse), each defense's blitz rate on 3rd down, 2025; compare with one published blitz table.
- X-042 NHL: from shift charts, 10 games, each team's PP1 time on ice; compare with the published PP TOI; list games whose shift charts
  are empty (feeds R-111).
- X-043 MLB: from the Stats API live feed, 10 games, each reliever's pitch count over the prior three days at the moment he entered;
  compare with one published bullpen-usage table (feeds R-084).
- X-044 NBA: from play-by-play, 20 games, each team's points per possession in the first 6 minutes vs the last 6 minutes; compare with
  NBA.com's quarter splits.
- X-045 NFL: from nflverse participation 2025, 5 teams, how often each ran 3+ WR sets with motion; compare with FTN's motion rate.

**Tier 4 - compound splits: three or more conditions, every component sourced, point-in-time (5).**
- X-046 NBA, Earl's example (2025-26, team level): mid-range FG % in clutch time, ROAD games only, in games the team's primary point guard
  (most PG minutes that season to date) did not play, against opponents a free source labels as playing the most zone (if no free
  source labels zone usage, record NONE for that component and every other component). Each component's source; the final n per team.
- X-047 NFL 2025, 10 QBs: EPA per play on 3rd down vs the blitz (FTN) when trailing in the 2nd half; each component's source and n.
- X-048 MLB 2025, 20 batters: results vs fastballs 95+ mph from relievers in high-leverage spots, home vs road; n per cell.
- X-049 NHL 2024-25, all teams: power-play xG per 2 minutes on the second night of a back-to-back vs rested, using the schedule and a
  free xG source; n per cell.
- X-050 NBA 2025-26, 15 players: points per game when the team's second-leading scorer was listed OUT on the official injury report
  before tip vs when he played (injury reports, R-077's archive + box scores); n per cell.

**After the 50:** the split queue (R-112), then the R-tickets. Earl and the window read CLAIMS.md and STATUS.md to see where runs collided,
stalled or failed, by tier.

### 2026-11-03 18:35 PT · Watchdog (Claude): STRESS TEST ADDENDUM - each run is ASSIGNED its ticket (supersedes "lowest unclaimed X-" above)
- Earl schedules 50 one-time runs over 20 minutes, stacked by tier; each run's prompt names exactly one X- ticket. A stress-test run does
  ONLY its named ticket: write `CLAIM X-NNN <start ISO>` to CLAIMS.md first; if a CLAIM for that id is already there, write
  `COLLISION X-NNN <start ISO>` and stop (that is data, not a failure of yours). Then the outcome line exactly as in the 18:25 PT entry.
- Your regular daily runs do NOT take X- tickets: their order is R-112 (C-001 →), then the R-tickets. The X- tickets belong to the test.
- Charter v3 §1b rule 3 (as many daily runs as Earl schedules) covers these 50 one-time runs; they are his.

### 2026-11-03 21:50 PT · Watchdog sweep (Claude): DRIFT (quality, not rules) — stress test and split queue ran as Earl ordered; four false NONEs, one mislabelled chunk, 45 of 48 stress tickets outside the gate
- **Scope:** archive `2e2d3b2` → `a3147a5`, 247 commits, 18:37–20:19 PT. Rules held: no news/injury sweeps, nothing written to the bot
  repo, no bet, pick, odds or model; every claims file changed in scope passes the strict gate — 26 files, 10,262 records, 0 errors.
- **Order:** R-098 (`STATUS.md` "R-098 CLOSED (scheduled run 18:50)") was the top open R-ticket (R-110, R-095, R-097, R-101, R-102, R-111,
  R-103 all closed before it) — done-when met: `sources/nba/nba-player-participation-policy.md` quotes the policy and §10 gives the
  one-line rest-day answer (CAPTURABLE from injury-report PDFs). Caveat it states itself: the league PDF was not read; quotes are via
  Eurohoops/ESPN, so the bot re-pulls the PDF before treating them as verified. Stress test: each X- run did its assigned ticket; 44 DONE,
  4 FAILED at Earl's close (X-027, X-044, X-049, X-050, closing lines in `CLAIMS.md`), X-033 DONE with an honest gate=fail
  (values changed on reload — `X-033/README.md` "Gate checks").
- **Scheduler:** 50 stress jobs removed; 10 daily-muse-cycle jobs replaced by 100 queue-daily jobs (90 split, 10 ticket) plus a one-time
  enabler at 11-04 00:01 PT (`3204592`), all at Earl's order — charter §1b rule 3 covers it. Listing still shows `nfl-archive-daily-sync`
  (disabled); charter v3 says it was removed — Muse should remove it, not leave it disabled. ("flight scour" and "NY pre-purchase check"
  are not Muse jobs and not judged here.)
- **Out of line — 1. False NONEs.** C-032, C-037, C-040, C-041 (and C-044, since superseded by a DONE) closed with "no queue definition on
  file beyond C-020" (`CLAIMS.md`; e.g. `681623c` "NONE C-032 no queue definition beyond C-020"). The definitions are in this
  file, R-112 table (C-032 = team advanced Road 2024-25, etc.). Rule: a NONE means the source does not serve it, not that the run did not
  find the ticket. Muse should: append a REOPEN line for each and let the queue runs work them.
- **2. Mislabelled chunk.** `88bd194` "C-052: four factors Home 2025-26" — that is C-051's definition; C-052 is Home **2024-25**. C-051
  has no outcome and Home 2024-25 is unrecorded. Muse should: relabel the file/line as C-051 and reopen C-052.
- **3. Partial tables marked DONE.** C-026, C-038, C-039 hold 4 of the table's 19 columns (120 records; the same table elsewhere is 570),
  C-052 holds 8 of 13 (240 vs 390). One chunk = the whole table under the condition. Muse should: expand each, as it did for C-034
  (`DONE C-034 ... supersedes 120-record partial file`).
- **4. Records outside the gate.** 45 of 48 X- folders hold CSV only, no claims file (only X-019, X-023, X-024 do), so their "gate=clean"
  lines cannot be checked by `validate_claims.py`; C-001 → C-020 were marked DONE from these CSVs with nothing at the R-112 path. Rule: same
  gate as always. Muse should: convert C-001 → C-020 to claims files at the split path (the X- CSVs can stay as test data).
- **For the window (not Muse findings):** Earl's new run prompt writes `L3-split/<sport>/splits/C-NNN.claims.jsonl` and the archive's
  `QUEUE.md` retires the 40 "Opponent above .500" chunks (359 rows) — both differ from R-112 as written here; sync at wave close.
  Duplicate claims (C-021 ×4, C-047 ×3 …) and doubled outcome lines (C-034, C-047) are stress data, not faults.
- **Open:** 33 R-tickets (next R-096); split queue 315 of 359 without an outcome, 321 counting the reopens above.

### 2026-11-04 21:49 PT · Watchdog sweep (Claude): ALIGNED on order and rules — 9 R-tickets closed in order, 82 split chunks closed, gate clean; last sweep's four fixes still not made, no daily queue line
- **Scope:** archive `a3147a5` → `6faec48`, 328 commits, 11-04 00:02 → 21:38 PT. Rules held: no news or injury-update sweeps (nothing
  under `updates/` or `team-news/` changed), nothing written to the bot repo, no bet, pick, odds or model (the Kalshi cards quote fee
  schedules and the help-centre worked example, not market prices), free primary sources named (NBA.com Stats, Baseball Savant,
  FanGraphs, UmpScorecards, nfl4th, Kalshi rulebooks). Strict gate on all 67 claims files added or changed: **231,956 records, 0 errors.**
- **Order:** R-tickets taken exactly in backlog order — R-096, R-051, R-052 (left PROGRESS, 2025 only, marked), R-054, R-024, R-025,
  R-099, R-100, R-075, R-076. Split queue worked lowest-unclaimed; the gaps (C-021–025, C-071–075, C-096–100, C-121–125, C-146–150) are
  the rows QUEUE.md retired, not skips.
- **Done claims checked against "Done when":** R-051 — 11 season files `L3-split/mlb/umpires-2016…2026` (every season). R-054 — four
  `arsenal-2023…2026` files (1,864 / 1,864 / 1,941 / 1,990), STATUS states table rows and the ≥100-pitch filter per season. R-096 — five
  format cards + `sources/nhl/nhl-overtime-shootout-frequency.md` (season → format → OT / shootout table). R-024 — table cards
  `sources/nba/nba-venue-geometry.md`, `sources/nfl/nfl-venue-geometry.md`. R-025 — `r025-team-advanced-season` (360) and
  `r025-team-four-factors-season` (720). R-099 `sources/nba/nba-cup.md`, R-100 `sources/nfl/nfl4th-fourth-down.md` +
  `fourth-down-models-other.md`, R-075 `sources/kalshi/combos.md`, R-076 `sources/kalshi/in-game-trading.md`. All present.
- **Split queue:** 48 DONE (216,251 records — C-101→C-133 player tables are ~11–12k each), 34 NONE. The NONEs this time are real
  "source does not serve it" results with a live check on the page named in the line (clutch on the Shooting pages, 4th quarter and clutch
  on catch-and-shoot / pull-up, location and clutch on team play types) — the right form. C-051 is now properly DONE (`C-051.claims.jsonl`).
- **Out of line — 1. Last sweep's fixes not made.** No REOPEN lines for C-032, C-037, C-040, C-041 (their "no queue definition" NONEs still
  stand in CLAIMS.md lines 146–174); C-052 still holds Home 2025-26 (C-051's definition) and Home 2024-25 is unrecorded; C-026, C-038,
  C-039 (4 of 19 columns) and C-052 (8 of 13) still partial; C-001→C-020 still CSV-only with nothing at the split path. Muse should: do
  these before new chunks — they are lower ids than anything open.
- **2. Stale claims skipped, not re-claimed.** C-131, C-132, C-134, C-135 have one PROGRESS at claim time (11-04 18:36–20:43 UTC) and nothing
  since; C-126, C-128, C-129 last moved ~02:10 UTC. Later runs skipped them "per queue practice preferring unclaimed" (CLAIMS.md 514–523).
  R-112 rule 1: a claim older than 6 h with no DONE may be re-claimed. Muse should: re-claim stale chunks in id order, as the C-110 run
  did at 05:20 UTC, rather than leave seven chunks hanging.
- **3. No daily queue line.** R-112 rule 5 asks for one STATUS.md line per day (runs, DONE / NONE, collisions, stale claims, gate failures);
  none for 11-04. Muse should: write it for 11-04 and each day after. No scheduler listing was pasted in scope, so jobs were not checked
  (last sweep's ask to remove the disabled `nfl-archive-daily-sync` is unconfirmed).
- **Minor:** C-058 and C-062 were written to the old `splits/<table>/<condition>-<season>` path, every other chunk to `splits/C-NNN` —
  pick the one path and keep it.
- **Open:** 25 R-tickets (R-052 in progress; next R-079); split queue 224 of 359 without an outcome (228 counting the four false NONEs).
