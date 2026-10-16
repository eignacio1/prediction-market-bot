# Thin-market price history — manifest (W78.2 Part A, PARTIAL)

Raw store (git-ignored): `exp_output/KALSHI_HISTORY/thin/raw_2026-10-16.jsonl`, 1,101,157,227 bytes, sha256 `b18fea086e4d4d794d92941aae2c7343e86a6eb2d707aed3726d11287e515f93` (W79.2, after adding KXNFLRSHYDS, KXNFLPASSYDS and NBA GAME/SPREAD/TOTAL/PTS/REB). Two copies, sha256 identical: operator laptop, and VPS `/opt/prediction-market-bot/exp_output/KALSHI_HISTORY/thin/` (verified 2026-10-16). W79.2 added 100 sampled markets each for those 7 families (settled: RSHYDS 9,083; PASSYDS 5,062; NBAGAME 2,836; NBASPREAD 18,459; NBATOTAL 16,174; NBAPTS 23,586; NBAREB 22,656). CI adequacy per family NOT yet assessed. Tool: `scripts/kalshi_thin_history_fetch.py` (resumable; stored kind+key skipped). Public GETs only. Kalshi keeps no historical order book: candles give bid/ask OHLC, volume, open interest; depth is not recoverable historically.

**Inventory** (`inventory.json`): 450 NFL/NBA non-annual series, 275 with settled markets since 2025-08-01, 310,858 settled markets, 0 series errors. Per-series strikes/event, first/last close, by-month counts.

**Candles fetched** (60-min over life + 1-min last 48h, deterministic hash-order sample of settled markets; includes 2026-season markets for custody only, no analysis may read them):
| Family | candle sets (2 per market) |
|---|---|
| KXNFLSPREAD | 500 (250 mkts of 10,805) |
| KXNFLTOTAL | 499 (250 of 8,472) |
| KXNFLTEAMTOTAL, 1HSPREAD, 1HTOTAL, ANYTD, FIRSTTD, RECYDS | 200 each (100 mkts) |

**Coverage gaps (not fetched):** KXNFLRSHYDS, KXNFLPASSYDS, all NBA families (GAME, SPREAD, TOTAL, TEAMTOTAL, PTS, REB). Sample is a fraction of each family. Run stopped at the session limit.

**Recurring capture (proposal, next wave):** one daily job over open NFL/NBA game-level series: list open markets, store the live orderbook for markets within 48h of close at fixed intervals plus candles after settlement. The orderbook snapshot is the only way to get depth, and it cannot be backfilled. Needs a RUNTIME_REGISTRY entry (Hard Rule 14).
