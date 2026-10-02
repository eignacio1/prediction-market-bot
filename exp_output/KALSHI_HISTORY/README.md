# exp_output/KALSHI_HISTORY — Kalshi sports history store (Wave 47 / 47.1 D4)

**STATUS: PARTIAL. Operator ended the session mid-fetch (2026-10-02); fetch killed, no background process left.**

Reader: `from prediction_market_bot.analytics.kalshi_history import prevailing_quote, settlement`
Builder: `scripts/kalshi_history_build.py` (`fetch` = public unauthenticated GETs at 1.5 req/s, halved on 429; `build` = pure
function of `raw/`, byte-identical on re-run). Tests: `tests/test_kalshi_history.py`.
Rule: close of latest candle with `end_period_ts <= t`, 1-minute first, hourly fallback (else None).

## Completeness (see VALIDATION.json for counts)
| Series | Markets (settled since 2025-08-01) | Candles |
|---|---|---|
| KXNFLGAME | 862 listed, normalized (850 validation ok, 12 flagged) | PARTIAL: 415 of 862 markets (1m+60m), ordered by ticker so Aug 2025 preseason onward only; 447 missing |
| KXNFLSPREAD, KXNFLTOTAL, KXNFLTEAMTOTAL | NOT FETCHED | NOT FETCHED |
| KXNHLGAME, KXNHLSPREAD, KXNHLTOTAL, KXNHLTEAMTOTAL | NOT FETCHED (KXNHLTEAMTOTAL has live endpoint only) | NOT FETCHED |

A ticker with no candle row returns None from `prevailing_quote`; `settlement` works for every market row present.
Do not read absence of a series as absence of markets. Resume: `python3 scripts/kalshi_history_build.py fetch` (idempotent,
skips stored candle keys), then `build`.

## Git tracking
`*.jsonl` is gitignored repo-wide. `raw/` (369 MB) and `candles/` (177 MB) are local only, not committed. Only
`markets/KXNFLGAME.jsonl`, `VALIDATION.json` and this README are tracked. Each row carries provenance: source_url,
retrieved_utc, content_sha256, runtime_commit_sha.
