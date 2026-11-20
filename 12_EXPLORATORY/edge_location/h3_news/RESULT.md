# H3 news latency — RESULT (W123.3, H-EDGE-3). Last reviewed: 2026-11-20
Run: `python3 -I run_h3.py --archive <PRICE_ARCHIVE>` (PREREG.md @ d698f99, frozen before any price was read). Muse pinned bf892b8
(NBA lineups 11-10..19, NFL inactives 4 days). Prices: Kalshi public trade prints (read-only, home-team YES on the game moneyline), last print
within 10 min. Output: results.json. Intervals: 90%, game-clustered, 2,000 draws. Unsigned moves (news direction is not known).

**Verdict: H3 NOT SUPPORTED on every NBA type that has n >= 30; UNDERPOWERED on NBA lineup confirmations and NFL inactives. Hypothesis closed for
NBA injury / scratch / starter-change news (EXP H3, parked for R&D). No market, family or sport closes.**

| Event type | Events (games) | Move still to come at +5 min, minus placebo [90% interval] | One round cost | Repriced within 1 / 5 / 15 min | Verdict |
|---|---|---|---|---|---|
| NBA injury: ruled out | 84 (40) | +0.45c [0.29, 0.61] | 1.84c | 94% / 95% / 98% | NOT SUPPORTED |
| NBA injury: day-to-day | 37 (25) | +0.30c [0.03, 0.63] | 2.02c | 89% / 95% / 100% | NOT SUPPORTED |
| NBA injury: other lines | 68 (38) | +0.28c [-0.00, 0.70] | 1.93c | 97% / 97% / 97% | NOT SUPPORTED |
| NBA starter-set change | 45 (33) | +0.46c [0.21, 0.71] | 1.90c | 89% / 91% / 98% | NOT SUPPORTED |
| NBA lineup confirmation | 6 (6) | +0.25c [-0.42, 1.00] | 2.10c | 83% / 100% / 100% | UNDERPOWERED (n 6, needs 30) |
| NFL inactives | 14 (14) | +0.14c [0.00, 0.29] | 2.00c | 100% / 100% / 100% | UNDERPOWERED (n 14, needs 30) |
| All NBA injury lines pooled | 189 (58) | +0.36c [0.20, 0.53] | 1.91c | 94% / 96% / 98% | NOT SUPPORTED |

Read: the price keeps moving a little after news (the intervals exclude zero for several types), but the part still to come at +5 min is 0.3-0.5c,
about a quarter of one round cost, and the median event is fully repriced inside the first minute (minutes-to-reprice: median 0, p90 0 for every
type; the share still moving by more than a round cost after 15 min is 0-3%). The decision rule needs a move larger than one round cost at +5 min; none is close.
Same shape as the NHL goalie result (W118.3, 0.2c, n 14): the news is in the price within a minute on the game moneyline.

Funnel (what dropped): NBA confirmations 60 -> 6 scored. Muse stamps a confirmation about 30 min before tip, so the pre-registered +30 min window
runs past the start for 54 of 60; I did not widen it after seeing this. Starter changes 102 -> 45 (57 past start), injuries 247 -> 189 scored
(55 past start, 3 without a print within 10 min), NFL 15 -> 14 (1 no market match). Placebo: 6,619 windows across 85 games.

Limits (each could hide a lag; none is tested here):
- Injury times are ESPN's posted clock minute, not when the first trader saw it; if the news broke earlier on X / beat reporters, the move is already
  in the price at t0 and a lag looks like zero. That is a limit of free timestamps.
- Moneyline only. Spread, total, team total and player-prop markets are touched by the same news and were not scored; props (less watched, H1) are the
  most likely place for a lag and need their own pre-registered test.
- Unsigned: the star-player value is not in a free column, so direction is not tested; unsigned |move| is an upper bound on a directional edge.
- Trade prints are last-trade prices in thin pre-game books; a print can sit stale up to 10 min by construction.

UNDERPOWERED needs: NBA confirmation: 30 events at the current yield (6 per 10 days of snapshots) is about 50 days, early January 2027, sooner if
Muse snapshots denser near tip (a snapshot at tip-60 min would put the window before the start). NFL inactives: 30 games = about two more full slates
(Sunday 11-29 and 12-06) if Muse captures every game's inactives; it captured 12 of 14 on 11-15 and 1 on each other day.
Routing: no news-reaction arm on the game moneyline for NBA injury / starter news; the leaf keeps its ride / no-bet arm.
Next test the data can support now: injury and lineup news on NBA player-prop and team-total markets (prints exist; archive prop series since 11-10).
