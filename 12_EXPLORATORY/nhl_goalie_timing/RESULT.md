# W118.3 Part B RESULT: goalie confirmation timing (EXP-W118.3-GOALIE). Last reviewed: 2026-11-18
Run: `python3 run_timing.py` (PREREG.md @ 9702cfe, committed before this ran). Muse snapshots f969ad1 (11-10..11-17), box-synced PRICE_ARCHIVE
KXNHLGAME 11-10..11-18. Output: results.json.

Funnel: 58 snapshot games, all 58 matched to a Kalshi event; 58 side-confirmations with a stamp; **14 eligible** (a snapshot within 25 min before the
stamp, all four post windows before 22:00Z game day). Most are lost to the archive's gap hours (no cron 05-11Z) and to confirmations the evening
before. Of the 14, only **2 are INFORMATIVE** (goalie name changed), 12 routine. 7,274 placebo windows (same games, no status change within 2 h).

| window after the stamp | event minus placebo, \|move in home yes_mid\| | 90% interval (game-clustered, 14 games) |
|---|---|---|
| +20 min | +0.0014 | [0.0000, 0.0029] |
| +40 min | +0.0071 | [0.0021, 0.0129] |
| +60 min (primary) | +0.0071 | [0.0021, 0.0136] |
| +120 min | +0.0071 | [0.0025, 0.0129] |
| lag: \|p(+120) - p(+40)\| | +0.0021 | [0.0007, 0.0043] |
Split at +60: routine +0.0083 [0.0025, 0.0155] (n 12); informative 0.0000 (n 2, no interval worth reading).

Read: the price does move after a confirmation, about 0.7 cent more than a quiet window, and most of that has landed by +40 min. The part after +40
min is 0.2 cent, below one round cost (mean half-spread 0.005, plus fee). Direction is not signed (no free goalie-quality column), so this is not a bet.
**Routing result: no lag the archive can trade; the split routes NO BET** (hypothesis closed: EXP-W118.3-GOALIE lag arm, parked for R&D).
Limits: n 14 / 2 informative is far below what a goalie-change effect needs; the informative split is where the information is, and it has two events.
Archive cadence is ~20 min, so a lag under 20 min is invisible. `confirmed_at_utc` is the site's stamp, not when a trader saw it.
Next (needs data, not a clock): the informative split needs ~30 changed-goalie events; Muse snapshots at 3 / day plus the archive reach that in
about 6 weeks of NHL; a goalie-quality column (save % above expected from the NHL store, once built) makes the direction testable.
