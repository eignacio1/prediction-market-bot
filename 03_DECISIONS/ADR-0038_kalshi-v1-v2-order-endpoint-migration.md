# ADR-0038 — Kalshi Order Endpoint Migration: v1 `/portfolio/orders` → v2 `/portfolio/events/orders`

**Status:** ACCEPTED — 2026-07-01 SESSION 108 (code shipped ahead of this ADR per operator-selected "migrate now, ADR after" option; DS ratification via this document)
**Decision makers:** DS (Earl Ignacio), drafted by EL
**Supersedes:** ADR-0008 §Decision item 2 (`submit_order()` endpoint and request schema only). All other ADR-0008 sections (RSA signing layer, governance constraints, degraded-mode behavior, local-ledger authority, rollback) remain in force unchanged.
**Superseded by:** —
**Related:** ADR-0008 (original write-capable venue integration), GG-063 (100% MLB order-failure discovery), GG-064 (new, DEMO `open_time` lag, OPEN)

---

## Context

GG-063 (SESSION 106) found that 100% of MLB Kalshi paper orders failed (T1 52/52, T4 15/15, all `"failed: HTTP 410"`), while NBA's historically identical `kalshi_client.py` code path showed a 73% success rate. SESSION 106 diagnosed but did not fix this — the response body driving the failure was discarded before reaching `submit_order()`'s error path, leaving only a bare `f"HTTP {r.status_code}"`.

SESSION 108 threaded the real response body through and re-ran the diagnostic. The actual body was:

```
deprecated_v1_order_endpoint
```

Kalshi has hard-deprecated `POST /portfolio/orders` (the v1 order endpoint ADR-0008 specified) platform-wide, returning HTTP 410 for every request regardless of ticker, account, or market. This is not a ticker-mismatch, eligibility, or demo-permissions issue — all three of those hypotheses (SESSION 106's leading candidates) were explicitly disproven this session (`GET /markets/{ticker}` returned HTTP 200 on both DEMO and LIVE for a live-fetched ticker).

NBA's 73% historical success rate is not evidence the code path still works — it predates Kalshi's v1 enforcement. A full breakdown of NBA's 158-bet history shows zero HTTP 410 failures ever recorded (`{'resting': 87, 'executed': 28, 'failed: HTTP 503': 18, 'failed: HTTP 429': 16, 'failed: transient...': 9}`). MLB's order flow began after Kalshi's deprecation took effect, so every MLB order hit the wall from day one while older NBA orders never did. This is a timing artifact, not a code-path divergence between sports.

Kalshi's published migration guidance (docs.kalshi.com/getting_started/order_direction.md) specifies the v2 replacement: `POST /portfolio/events/orders`. This ADR authorizes and documents that migration.

---

## Decision

**`submit_order()` in `kalshi_client.py` is migrated from `POST /portfolio/orders` (v1) to `POST /portfolio/events/orders` (v2).** ADR-0008 §Decision item 2 is amended accordingly; every other ADR-0008 provision (RSA-PSS signing, degraded-mode local-ledger authority, demo-only scope, rollback procedure) is unchanged and still governs.

Schema changes, per Kalshi's published legacy→v2 mapping (this bot only ever buys, so the mapping collapses to two cases):

| v1 field | v2 field | Notes |
|---|---|---|
| `side: "yes"` / `"no"` | `book_side: "bid"` / `"ask"` | `side="yes"` → `bid` (buy-yes); `side="no"` → `ask` (buy-no). Sell-side mappings exist in Kalshi's docs but are inapplicable — this bot never sells. |
| `count: <int>` | `count: "<int>.00"` | Fixed-point decimal string, not a JSON integer. |
| `price: <int cents>` | `price: "<dollars>.<cents>"` | Fixed-point decimal dollar string (e.g. `52` cents → `"0.52"`), not integer cents. |
| — | `time_in_force` (new, required) | Set to `"good_till_canceled"`. |
| — | `self_trade_prevention_type` (new, required) | Set to `"taker_at_cross"`. |

**Error-body threading (originally scoped under GG-063/T-217, shipped as part of the same fix):** `_post()` already captured the real Kalshi response body under `data["body"]` (HTTP error) or `data["detail"]` (exception) but `submit_order()`'s error path only surfaced `data.get("error", data)`, discarding it. This is corrected — `error_detail` is now appended to `error_msg` whenever present, so future failures surface Kalshi's actual rejection reason instead of a bare status code. This is the fix that made the v1-deprecation root cause discoverable in the first place, and remains valuable independent of this migration for diagnosing whatever failure mode appears next.

---

## Verification performed this session

A manual test order was submitted against Kalshi DEMO with a live-fetched KXMLBHIT ticker under the corrected v2 request body. Result: the error type changed from **410 (`deprecated_v1_order_endpoint`)** to **409 (`market_closed`)** — the v1 deprecation wall is gone; the new failure is unrelated (all 60 open KXMLBHIT DEMO markets at test time had `open_time` in the future — see GG-064 below).

**Full 200/201 order confirmation was not obtained this session** — no genuinely open/active KXMLBHIT market existed in the DEMO order book at test time to submit against. This is tracked as a new, separate, open item (**GG-064**, OPEN, LOW priority, zero capital risk) — not a residual GG-063/ADR-0038 concern. Closing GG-064 requires observing the next real T1/T4 MLB cron run's `kalshi_order_status` distribution against markets confirmed `active` on Kalshi LIVE.

Test suite: 52/52 `kalshi_client.py`-specific tests pass under the v2 schema. Full suite unaffected by this change (17 pre-existing failures belong to a parallel session's unrelated T-212 fixture work).

---

## Governance constraints (unchanged from ADR-0008, restated for clarity)

- **ENV guard preserved**: `BOT_ENV=paper` still required; order submission still follows `BOT_ENV`, market/price data still always hits LIVE production (T-114).
- **Local ledger remains authoritative**: `paper_portfolio_mlb.json` / `paper_portfolio.json` are still the G6 evidence source. Kalshi confirmation — now that it can actually succeed — is corroborating evidence, not a replacement. No G6 sign-off narrative should cite MLB Kalshi-side confirmation until GG-064 closes with an observed 200/201.
- **Degraded mode unchanged**: Kalshi order failure still does not halt the bot; local position is still recorded with `kalshi_order_status = "failed: <reason>"` (now with the real Kalshi rejection text appended).
- **Demo account only**: unchanged from ADR-0008 — live account key must not be used until G6 clears.

---

## Rollback

If the v2 endpoint migration causes unexpected behavior:
1. Revert `kalshi_client.py`'s `submit_order()` to the prior commit (v1 body/endpoint) — this restores the known-bad HTTP 410 state, so this is a diagnostic rollback only, not a recommended operational fallback.
2. No other files depend on the v1/v2 distinction; `PaperTrader`, `run_mlb_paper_trade.py`, `run_t4_mlb_live.py`, and NBA equivalents call `submit_order()` through the same interface regardless of which Kalshi endpoint it targets internally.
3. All prior paper positions remain valid in their respective ledgers — the local ledger was never dependent on Kalshi order success (ADR-0008 degraded-mode guarantee).

---

## G6 implications

Unchanged in kind from ADR-0008: this does not alter G6 gate criteria (30 resolved bets, positive P&L, ADR-0005, EXP-017/GG-004). It restores the external-confirmation evidence channel ADR-0008 established, which had been silently broken for all MLB orders since inception. Until GG-064 closes with an observed successful order, treat MLB's external-confirmation evidence as **not yet demonstrated**, only unblocked.
