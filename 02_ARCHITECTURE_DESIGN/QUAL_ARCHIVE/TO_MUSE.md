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
