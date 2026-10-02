# EXP-034 D1 findings (2026-10-02) — in progress; D1(b) comparison NOT yet run

D1(a), observed:
- /historical/cutoff: market_settled_ts 2026-08-03; markets settled earlier are served only by /historical/markets/{t}[/candlesticks]; later by live /markets.
- Candle intervals 1, 60, 1440 min. Daily candles for KXCPI-26JUN-T-0.3 reach back to market open (2026-06-08): lookback = full market life.
- 1-min candles are SPARSE (minutes with no change are absent). Live candles: 1-min row 1 shows empty-book placeholder (ask 0.99/bid 0.00) at open.
- Null prices: live `price` = {} when no trade; historical `price.*` = null with `previous` populated. Zero-volume candles common (quote-only).
- SCHEMA DIVERGENCE: live = `*_dollars`/`*_fp` keys (volume_fp, open_interest_fp); historical = bare keys (`volume`, `open_interest`, `yes_bid.close`). A shared parser must handle both.
- No Retry-After / X-RateLimit-* headers on 200 responses (docs: 429s carry none either; exponential backoff).
D1(c) fee: ADR-0016 model 0.07*p*(1-p); /series/KXHIGHNY fee_type=quadratic, fee_multiplier=1; rounding mechanics per Kalshi docs fee_rounding.
  EXACT REFUSAL: https://kalshi.com/docs/kalshi-fee-schedule.pdf -> HTTP 429, `x-vercel-mitigated: challenge` (Vercel Security Checkpoint), retried once after 20s, same result. Not bypassed. Fee schedule PDF therefore UNREAD; maker/taker split is documented only via the OpenAPI fee_type descriptions. 
D1(b): tolerance frozen in D1B_TOLERANCE_PREREG.md (commit 38b8490); sampler running, round 0 captured 19:33Z.
