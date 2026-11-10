# W106.3 (B-058) — Retail flow: props and thin markets, net of costs — EXPLORATORY, not a verdict

Data: public price archive (Aug 1 – Nov 2026, ~20-min snapshots) + public Kalshi settled results (`/markets`, `/historical/markets`; 251,528 settled tickers across 6 MLB series). Entry = first two-sided pre-start snapshot per (ticker, time-to-start tier); taker at the quote (YES at ask, NO at 1−bid), exact `fee_k007`, held to settlement. Fit on the earlier 70% of games, side chosen on fit only, scored on the later 30%; game-clustered bootstrap 95% intervals; Holm across all cells with ≥30 held-out games. n = 116,675 priced-and-settled rows, 50 cells (≥200 rows). Reproduce: `run_props.py` (`results.json` beside this file).

## Plain English

**MLB — props are NOT mispriced after costs, and neither are the game lines.** Of 50 family × price-band × liquidity cells, **zero** is net positive held-out after Holm (the best, KXMLBF5TOTAL >90c deep, is +2.3c/contract [+0.2, +4.2] raw p=0.015 but Holm-adjusted p=0.74: one hit in 50 looks is what chance gives).
- **Player hits (KXMLBHIT, 41,770 rows, 214 held-out games):** raw mispricing exists — outcomes beat price by +1.2c on average [+0.6, +1.9] (mostly the <10c longshot band: +0.9c [+0.3, +1.4]; the favourite-longshot shape here is *longshots underpriced*, not overpriced) — but it is smaller than the cost: held-out net **−1.4c/contract [−2.7, +0.0]**. Thin-book cells lose the most (30–70c thin −8.5c [−12.5, −4.1]).
- **Game lines on the same 81 nights (74,839 rows, 1,188 held-out games):** net **−3.2c [−5.0, −1.4]**; gap +1.1c [+0.2, +2.1]. The prop-vs-line difference in raw gap is within noise (+1.2c vs +1.1c), so **"mispricing is larger where retail trades" is not supported on this data**; props lose *less* net than lines mainly because their quoted spreads are tighter in the cells that matter.
- **Thin books are expensive, not mispriced:** in every family, "thin" (half-spread > 2.5c) cells lose 8–20c/contract held-out; the spread eats whatever bias exists.

**NBA / NFL / NHL props — NOT MEASURED. This is a gap, not a "no."** The archive holds exactly one prop family (KXMLBHIT). KXNBAPTS, KXNFLPASSYDS and the other prop series are listed live (NBA: 3PT/AST/BLK/PTS/REB/STL; NFL: pass yds/att/comp/TD, rec, rec yds, any/first TD; NHL: goals/assists/points/saves) but nothing archived their pre-start prices, and settled markets expose only post-resolution prices. Fix = start archiving those series (needs a task + approval; named in the handoff). No forward data waited on.

## Caveats (stated, not hidden)
- MLB regular-season/post-season only; one sport's prop family generalizes to nothing else yet. Sample is ~3 months.
- Liquidity tier here = quoted half-spread class (deep ≤1c, mid ≤2.5c, thin >2.5c); the archive's depth files give family medians (below) but not per-snapshot sizes for every ticker.
- Entry is the first snapshot per tier, a research convention; real fills face queue/slippage, so true net is likely worse.
- Clustering by event ticker; KXMLBHIT events hold many players, so effective n is games, not rows.
- Holm applied over 49 cells with ≥30 held-out games; other cells descriptive.

## Granularity index / ADR-0075 stage
Factor: price level × liquidity × time-to-start × market class. Stage: **interpreted** (split + cost-aware net; no tested path to a price, so not "applied"). Tails: <10c and >90c bands reported; no cell with a positive held-out tail edge survived correction.

## Pre-registration
None written: no cell is net positive held out after multiplicity correction (Part C condition not met). Nothing for Wave 107 router ride/pot-of-gold tables from this look except: do **not** seed MLB prop or thin-book cells on a mispricing theory.
