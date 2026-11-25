# EXP-NHLDEPTH-001 — NHL depth: goalie confirmation, referee crew, availability as tested splits (pre-registration)

**Last reviewed:** 2026-11-24 (W128.1, B-122). **Status:** pre-registered, committed before any outcome (final score, margin, total, settlement)
is joined to any leaf. Docs-only commit. Doctrine: DOCTRINE.md §1 (ADR-0077), COMMON_RULES_W128.

**Measure moved:** DEPTH D5(b), NHL factor classes by stage. Before: NHL-9 officials, NHL-10 coaches/scratches, NHL-11 availability, NHL-12
qualitative = `none`; NHL-2 goalie quality uses the starter known only after the game. A factor is *applied* when it is a tested split scored
per leaf on net after costs, held out, per arm. A tested null is a routing result ("ride / no bet in these leaves"), not a stop.

## 1. Splits (leaf definitions fixed now)
| Split | Seat | Leaf | Input, point-in-time |
|---|---|---|---|
| G goalie confirmation | NHL-2 / NHL-10 | per team: `confirmed_expected` (published starter = team's most-played goalie in its prior 10 games), `confirmed_backup` (published starter is not), `unconfirmed` (status not "confirmed" at snapshot). Game level: `both_expected`, `any_backup`, `unknown`. | Muse archive goalie snapshots (`eignacio1/sports-intel-archive`, pinned SHA `ab9951c37958af812fd170c544399cf75825d561`, GitHub API only). Usable only if `snapshot_at_utc <=` the row's `ts_utc`; latest such snapshot wins. Status as published, never revised. |
| R referee crew | NHL-9 | crew prior = mean (total goals − total line) over the crew's referees' earlier games in 2026-27 only, shrunk to zero with k=20 crew-games; terciles by the fit rows: `ref_high`, `ref_mid`, `ref_low`. No prior games → `unknown`. | Muse referee-crew snapshots (same pin, same PIT rule); NHL free game pages as a cross-check only. |
| A availability | NHL-11 | skaters out among the team's top-6 by prior-10-game TOI: `none`, `one`, `two_plus`. Game level: differential home−away `≥+1`, `≤−1`, `even`. | **No point-in-time source in the archive today** (no availability/injury family). Pre-registered as ABSTAIN unless the NHL free API supplies a timestamped pre-puck-drop list; otherwise every row is `unknown` and the stage stays `none`. Never imputed. |

NHL-12 qualitative: no input exists; not built, stage stays `none`.

## 2. Markets, prices, arms
- **Markets:** KXNHLGAME (moneyline, both sides), KXNHLTOTAL, KXNHLSPREAD; one pre-game entry per market-side at the last price-archive snapshot
  before puck drop and at least 30 minutes before it.
- **Arms per leaf:** RIDE (back the market-favoured side at the ask), FADE (the other side), MOMENTUM (side the price moved toward over the prior
  6 hours), POT_OF_GOLD (longshot side priced ≤15¢), NO_BET. Arm outcome per contract = payout − ask − `fee_per_contract(series, price)` −
  half-spread; gross, cost and net reported side by side.
- A leaf is a tested split only if it carries `MIN_N = 30` games per arm in the held-out half.

## 3. Population and design
- 2026-27 regular-season games from **2026-11-10** onward (Muse snapshot coverage starts 11-10). Earlier rows are not used. Fit half = earlier
  games by date, held-out half = later games; leaf thresholds (terciles) are set on the fit half only.
- Partial pooling across leaves within a split and arm (`quant.variance.partial_pool`), game-clustered bootstrap (`quant.inference.cluster_bootstrap`,
  B=2000, seed 20261002), Benjamini-Hochberg q = 0.10 across all split × leaf × arm tests. A KEPT verdict needs the pooled lower bound > 0 net,
  BH-passing, on the held-out half; otherwise DRAFT/null.
- Data epoch: NO-side demo fills before 2026-11-06T01:03:42Z were mirror-priced and are excluded. Price-archive prices are proxies, not
  tradable fills; no verdict here is execution evidence.

## 4. Power (`quant.variance.games_needed`, sd 0.5 per contract, 2 rows/game, icc 0.2, one-sided α 0.05, power 0.80)
Games needed to detect a true net per-contract effect of 2¢ / 3¢ / 5¢: **2,318 / 1,030 / 371** (Bonferroni α/3: 3,307 / 1,470 / 529). With 60 games
the MDE is 12.4¢; with 100 games, 9.6¢. An NHL slate gives roughly 6 games a day, so the 2026-27 sample from 11-10 reaches ~100 games around
early December and ~370 only near the end of January.

## 5. Modal outcome (stated before the data)
- **G, R:** "not judged: n below MIN_N / below games_needed". The splits are built and logging; leaf counts and games-needed are reported; no
  routing is changed. Probability of a KEPT verdict on any leaf at the first look: < 5%.
- **A:** abstain (no point-in-time feed). Stage unchanged.
- A tested verdict is declared only where the above bar is met. Stages in SEATS/nhl.toml move only for such splits; a split that is built but
  unjudged is reported as "built, shadow, unjudged", not as applied.

## 6. Kill / hypothesis closure
A losing look closes only that hypothesis ("hypothesis closed (EXP-NHLDEPTH-001-<split>, parked for R&D)"); no cell, market or arm closes.
Kelly stays 0; shadow only; orders follow v1.
