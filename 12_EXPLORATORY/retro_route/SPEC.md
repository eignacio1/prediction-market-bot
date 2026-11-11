# W110.5 retro-route — frozen spec (committed BEFORE any result is computed)

Purpose: D6 / PROOF. Score every settled shadow row by ARM, per leaf, net after costs, held out. Doctrine §1/§1b:
a leaf that loses on an arm is ROUTED away from that arm. A model-vs-market number is reported last.

## Data (exists now; nothing future)
- Shadow ledgers NFL/NBA/MLB (`PREGAME_SHADOW/settled`, outcome `y`) and NHL (`data/shadow/nhl` raw rows joined to `settled` `outcome` on (market_ticker, run_id)). Paper/shadow rows, not fills: the GG-1771 fill epoch does not apply.
- Dedupe: one row per (market_ticker, run_id). MONEYLINE: the two tickers of a game are one bet; keep the higher-mid ticker per (event, run_id).
- Cluster id = game (event_ticker minus series prefix). Move since open / last hour come from the same ticker's earlier shadow rows (archive join is a registered gap, see handoff).

## Arms (taker, hold to settlement, exact fee `quant/money.fee`, phase prelive; the taker price is the ask / 1-bid so the quoted spread is already paid)
RIDE = buy the favoured side (mid >= .5 -> YES). FADE = buy the other side. MODEL-FADE = buy a side only if model p exceeds price + exact fee. MOMENTUM = follow the sign of the mid change vs the ticker's previous row (|move| >= 0.005). NO BET = 0.

## Leaves
cell (sport x market type) x band (T1/T2/T3) x favoured-side price bin [<.35, .35-.5, .5-.65, .65-.8, >=.8] x move bin {down, flat, up, na}.
Factor filters (110.1 / 110.2) are not importable per-row from shadow data: registered as a gap, not stubbed with fake values.

## Fit / test
Games ordered by start date; earliest 70% of games = fit, latest 30% = held out. Per leaf the fit picks the arm with the best fit mean net per contract if > 0, else NO BET.
Minimum n (fixed before looking): fit >= 60 rows AND >= 20 games, else the leaf is NO BET by default ("thin"). Held-out result is reported only at >= 10 held-out games.
Interval: game-clustered bootstrap, 2000 resamples, seed 110, 90% two-sided. Multiplicity: one-sided bootstrap p per routed leaf, Benjamini-Hochberg q = 0.10 across all routed leaves with reportable held-out n.
Pre-registration DRAFT only if: BH-significant AND held-out lower 90% bound > 0 AND >= 15 held-out games. Drafts are forward-test proposals (judged n), not live; no cell status changes.
