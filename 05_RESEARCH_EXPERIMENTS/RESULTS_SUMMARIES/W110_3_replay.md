# W110.3 Part C -- router replay, last 14 archive days (NULL result)

Source: `exp_output/PRICE_ARCHIVE/prices_2026-10-29..2026-11-11.jsonl`, series NBA/NHL/NFL GAME, SPREAD, TOTAL.
One decision per (ticker, tier) at the first snapshot in that tier. Evidence = ride table only. Data epoch: no fills
are used; this is a book replay, so the NO-side mirror-price epoch (2026-11-06T01:03:42Z) does not apply.

| | n |
|---|---|
| decisions | 25,263 (NBA 15,169; NFL 4,746; NHL 5,348) |
| RIDE | 0 |
| POT_OF_GOLD | 0 |
| FADE / MOMENTUM | 0 (no skill record, no momentum table for these families) |
| NO_BET | 25,263 |

NO_BET reasons: date_only_game_day 10,673 (42%); price outside the pot-of-gold buckets 9,908; no longshot cell 1,732;
no two-sided book 1,946; started/unparseable 897; ride cell present but IN_SAMPLE 48+59.

Gross/net per branch: not computable -- no branch emitted a side, so n = 0 scored. No settlement lookup was needed.
Reading: with today's cell tables the router declines every NBA/NHL/NFL game-family situation in this window. The two
binding causes are date-only tickers (tier D0 is disqualified by design) and cells that are IN_SAMPLE, not HELD_OUT.
A null, not a failure. Reproduce: `scripts/replay_router_w110_3.py` (JSON beside this file).
