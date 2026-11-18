# W117.2 RESULT — NHL consensus history (B-099). Last reviewed: 2026-11-18
Source: Muse archive @ 018634eca5555e3ab1936862b9842bf850e63084, minmaxxxer-2025-26 (CC-BY-4.0), file sha256 verified in the loader.
Pre-registration: PREREG.md @ 2a45e52, committed before any outcome statistic. Corpus for the calendar: the local W110.5 snapshot
(108,439 rows after dedupe; RESULT.md of W116.1 used 106,430, so first-arm dates here differ by 1-2 weeks from that file; the nfl-only run
below is the like-for-like baseline).

## A. The prior (regular season, favourite side, realised net at the consensus close = gap; fade = -gap)
| bin | n | gap (ride net) | se |
|---|---|---|---|
| NHL_MONEYLINE fav-bin 2 | 1,167 | -0.0328 | 0.0146 |
| NHL_MONEYLINE fav-bin 3 | 145 | +0.0046 | 0.0382 |
| NHL_PUCK_LINE fav-bin 2 / 3 | 750 / 562 | +0.0381 / +0.0507 | 0.0175 / 0.0189 |
| NHL_GAME_TOTAL fav-bin 2 | 1,266 | +0.0213 | 0.0140 |
Transfer SD 0.03 (book close to Kalshi mid), applied by the runner exactly as for nflverse. One season only, so the se is the real limit.

## B1. Momentum (open-to-close move past the close; game-clustered 2,000-bootstrap, 90% interval, regular season)
| market | n | beta | 90% interval | verdict |
|---|---|---|---|---|
| moneyline (prob move) | 1,312 | -0.86 | [-4.29, +2.86] | hypothesis closed (EXP-W117.2-MOM-moneyline, parked for R&D) |
| puck line (line move) | 1,312 | -0.04 | [-0.155, +0.060] | hypothesis closed (EXP-W117.2-MOM-puck_line, parked for R&D) |
| total (line move) | 1,266 | -0.14 | [-0.475, +0.178] | hypothesis closed (EXP-W117.2-MOM-total, parked for R&D) |
No market shows an under-reacting close. Limits: the file has no open cover or over probability, so puck line and total test a line move;
the moneyline move is small (sd 0.026), so its interval is wide and the test has little power. Playoffs (n=82/82/72) are descriptive: the
moneyline interval sits above 0 but on 82 games; it binds nothing.

## B2. Kalshi vs books (moneyline only; last hourly candle at least 1h before start; spread <= 0.10)
Overlap: 1,312 of 1,312 regular-season games (playoffs 80 of 82) match a KXNHLGAME event by date and team pair; all have an eligible price.
- Gap (Kalshi mid minus consensus close, home side): +0.0016 [+0.0011, +0.0020]; sd 0.0094. Kalshi sits on the books at the close.
- Ride the consensus favourite, Kalshi ask plus taker fee: net -0.0548 per contract [-0.0773, -0.0314].
- The other side (fade the consensus favourite) after the same costs: +0.0080 [-0.0149, +0.0309]. This is the one-season favourite shortfall
  (gap -0.033) minus Kalshi costs; the interval spans 0.
- Puck line and total: no Kalshi history for 2025-26, so not testable here. 2026-27 need registered in TO_MUSE.md (722 games per market).
Caveat: candle price is the hour before start, not the exact consensus-close instant, and the cache is the w84-3 worktree (not on main).

## C. Power calendar (first arm date, router v2; a node alone at a fixed true net)
| sport, leaf level | none | own prior | prior moved |
|---|---|---|---|
| NHL +0.02 | 2027-08-04 | 2027-07-14 (nhl) | 3 weeks earlier |
| NHL +0.05 | 2027-01-27 | 2027-01-20 | 1 week |
| NFL +0.02 | 2028-09-27 | 2028-08-09 (nfl) | 7 weeks |
| NFL +0.05 | 2027-04-21 | 2027-04-14 | 1 week |
Level, NHL, both priors, +0.02 / +0.05: family never / 2027-07-07; band 2028-02-02 / 2027-03-17; price bin 2027-07-28 / 2027-01-20; leaf 2027-07-21 / 2027-01-20.
Level, NFL, both priors: family never / 2027-10-27; band never / 2027-08-11; price bin 2028-06-28 / 2027-03-31; leaf 2028-08-09 / 2027-04-07.
Coarse leaves do not pull the date in: a family or band node is a mixture of prices, its per-game variance is higher, and the same assumed net is
harder to see. They are 6 to 40 weeks LATER than the price-bin or leaf level (family never earns at +0.02). The prior is the lever that moved it:
1 to 7 weeks earlier. Neither moves the first arm out of 2027. Cross-sport pooling means one sport's prior shifts the other's date by up to 2 weeks.
