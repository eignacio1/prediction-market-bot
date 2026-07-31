# Phase 0-A Parking Notes

## Environment question — RESOLVED (2026-07-31)

`kalshi_client.py:338` (`_get()`) routes unauthenticated market-data endpoints
(`/series`, `/markets`, `/markets/{ticker}/orderbook`) to production
**unconditionally**, via `_price_discovery_url()` (kalshi_client.py:104-110),
regardless of `BOT_ENV`. Only authenticated portfolio/order endpoints
(`_kalshi_base_url()`, kalshi_client.py:98-101) follow `BOT_ENV` routing.

**Implication:** `series_all.json` and `markets_sample.json` (this capture) are
genuine production data — no re-capture needed. Orderbook depth sampling via
`scripts/phase0_market_survey.py depth` is likewise production-scoped and safe
to run under any `BOT_ENV` value.

**Only the `usage_tier=basic` reading in `account_limits.json` is demo-scoped**
— it came from an authenticated call (`/account/limits`) made under
`BOT_ENV=ENV-01`, which routes to the demo sandbox. See GG-152 (registered
this session) for the underlying `BOT_ENV` vocabulary mismatch that causes
this, and `02_ARCHITECTURE_DESIGN/VENUE_REGISTRY.md` V-001 for the corrected,
demo-scoped recording of the tier reading.

## Open items carried forward
- GG-152 (OPEN, G6 precondition): `_kalshi_base_url()` never recognizes the
  documented `ENV-03` (live) value — silently routes to demo. Needs operator
  sign-off before fixing; touches live-capital/order-submission path.
- Unresolved side-note in GG-152: `.env.example:22` says venue keys are
  "ENV-02/ENV-03 only, NOT set in ENV-01," but this session's capture ran
  fine under `ENV-01` with keys present. Comment or convention is stale —
  which one, is not yet determined.
- Production account's real rate-limit tier is still unmeasured. Do not cite
  `usage_tier=basic` as the live tier anywhere until re-captured under
  correctly-routed live auth (blocked on GG-152 being resolved first, since
  fixing the routing is a live-capital-path change).
