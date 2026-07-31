# Venue Registry — CA-Eligible Prediction Markets

**Purpose:** Register all target venues for this system — mechanics, regulatory basis, CA eligibility, pricing structure, edge formula, and activation status.
**Owner (role):** Architecture Owner (AO)
**Status:** CANONICAL (2026-05-29)
**Last reviewed:** 2026-07-31 (Phase 0-B depth survey — added measured orderbook depth per market family (first-ever traced measurement, `depth_sample.json`), the $25,000/contract position limit (Rulebook 5.14(a)), and corrected the prior "$500-$2,000 depth" claim for KXMLBHIT-class markets, which was never sourced and is contradicted by the measured data: real median depth for that family is $0.90, see GG-155). Prior review: 2026-07-02 (documentation-remediation pass — added the MLB KXMLBHIT series and fee-rate caveat this document was silent on; also note the Kalshi order endpoint migrated v1→v2, `/portfolio/events/orders`, per ADR-0038 SESSION 108 after Kalshi deprecated v1 platform-wide). Prior substantive review: 2026-05-29 (initial build — Phase 6 idle period)
**Next review:** On any new venue activated; on API change; on regulatory status change
**Staleness triggers:** Venue added or removed; regulatory change; API version change; ADR update
**Upstream links:** STRATEGY_OVERVIEW.md; ADR-0003 (venue selection); INTERFACES_CONTRACTS.md
**Downstream links:** venue_adapter.py (implementation); venue_router.py (routing); ENVIRONMENTS.md (API keys)
**Decision references:** ADR-0002 (forecast-only); ADR-0003 (Kalshi primary; Polymarket secondary)
**Confidence:** 8/10
**Decisions logged:** true — T-096 logged 2026-06-02: V-001–V-005 priority order and rationale, activation gates, edge formula per venue type (CFTC vs. DFS). See DECISION_LOG.md 2026-06-02.

---

## CA Eligibility Context

California has no legal retail sports betting (Prop 26/27 both failed). The eligible venue universe for CA residents:
- **CFTC-regulated prediction markets** — federally regulated; available all 50 states
- **DFS pick'em platforms** — legal under CA's professional sports fantasy game carve-out
- **Traditional sportsbooks (DraftKings, Caesars, FanDuel)** — NOT CA-eligible; excluded from scope

---

## Venue Registry

### V-001 — Kalshi

| Attribute | Value |
|-----------|-------|
| Type | Binary prediction market |
| Regulatory basis | CFTC-DCM (Designated Contract Market) — federally regulated |
| CA eligible | Yes — all 50 states |
| ADR status | ADR-0003 ACCEPTED — primary venue |
| Activation | ✅ LIVE (ENV-02 VPS; PIPE-02/03 running) |
| API | `api.elections.kalshi.com` — REST; Bearer token auth |
| Current key | ACC-0002 (read-only); ACC-0003 (write — Phase 8, ADR-0005) |
| Pricing structure | Dynamic supply/demand; binary YES/NO; $0.01–$0.99 |
| Settlement | $1.00 (YES wins) or $0.00 (NO wins) |
| Vig | ~3% confirmed for NBA (EXP-010: vig = 0.030). **MLB fee rate NOT independently confirmed** — 0.07×p×(1−p) assumed per marketmath.io + one corroborating source, one conflicting source suggests ~0.06 for sports markets specifically; GG-020 OPEN, no live receipts exist to settle it (paper trading only). Direction of error if 0.06 is correct: conservative (over-deducts fees, rejects some profitable bets at the margin). |
| Series used | KXNBAPTS — NBA Player Points. **KXMLBHIT — MLB Player Hits, added when MLB C1 unblocked (T-072, SESSION 73) — this row previously listed NBA only.** |
| Edge formula | `edge = p̂ - mid_price` (market-priced) |
| Adapter | `KalshiVenueAdapter` (`c5_execution/venue_adapter.py`) |
| implied_prob_method | `market` |
| Connectivity | Datacenter IP required (CloudFront WAF blocks home/work ISP) |
| Rate limit tier (DEMO account, unverified for production) | `usage_tier=basic` — read bucket 400 cap / 200-per-sec refill, write bucket 100 cap / 100-per-sec refill. Source: `GET /account/limits`, captured 2026-07-31 (Phase 0-A, `exp_output/PHASE0_SURVEY/account_limits.json`). **This call ran under `BOT_ENV=ENV-01`, which routes authenticated endpoints to the demo sandbox (`kalshi_client.py:98-101`) — it is the demo account's tier, not production's.** The production account's tier is unknown and unmeasured; do not treat this figure as the live limit until re-captured under `BOT_ENV=ENV-03`/live routing (see GG-152). Unauthenticated market-data reads (`/series`, `/markets`) are unaffected by this caveat — they route to production unconditionally via `_price_discovery_url()` regardless of `BOT_ENV`. |
| Position limit | **$25,000 per contract** (Kalshi Rulebook 5.14(a), sourced in `02_ARCHITECTURE_DESIGN/MARKET_UNIVERSE_SURVEY_SPEC.md`). Does not bind today — `_HARD_LIMITS["max_single_event_exposure_usd"]=500.0` (`risk.py`) is 50x inside it — but it is the true external ceiling, distinct from the measured orderbook-depth ceiling below. |
| Measured orderbook depth — basic, DEMO-SOURCED (Phase 0-B, 2026-07-31) | See table below. Sampled live via `GET /markets/{ticker}/orderbook`, 20 markets/family, `exp_output/PHASE0_SURVEY/depth_sample.json`. **This corrects CLAUDE.md's prior unsourced "$500-$2,000 depth" claim for KXMLBHIT-class markets** — that figure was never traced to a measurement and this survey is the first one. The real number is far below it: `PLAYER_PROP` (the family KXMLBHIT/KXMLBHR/KXMLBRBI/KXMLBKS classify into) measured a **median of $0.90 and a minimum of $0.00** notional absorbable within 5c of mid, across 3 usable books out of 20 sampled (17/20 had no two-sided book at all). This fails even the survey's own $10 depth-gate floor (10x the $1.00 ADR-0050 measurement stake), let alone the $500-$2,000 range CLAUDE.md asserted. See GG-155. |

**Measured depth by family (Phase 0-B, sampled 2026-07-31T20:13:03Z, `depth_sample.json`):**

| Family | Sampled | Usable | Median within-5c depth (USD) | Min depth (USD) | Gate ($10 floor) |
|---|---:|---:|---:|---:|---|
| GAME_TOTAL | 20 | 20 | 0.0 | 0.0 | **FAIL** |
| GAME_WINNER | 20 | 20 | 1,646.50 | 0.0 | PASS |
| PARTIAL_GAME_WINNER (KXMLBF3/F5/F7) | 20 | 17 | 410.99 | 156.96 | PASS |
| **PLAYER_PROP (KXMLBHIT/KXMLBHR/KXMLBRBI/KXMLBKS)** | 20 | 3 | **0.90** | **0.00** | **FAIL** |
| RUN_LINE | 20 | 20 | 0.0 | 0.0 | **FAIL** |
| SEASON_WIN_TOTAL | 20 | 10 | 5.96 | 0.42 | **FAIL** |
| TEAM_TOTAL | 20 | 20 | 2,043.53 | 882.70 | PASS |

Scope caveat: sampled from Phase 0-A's 220-series "MLB-looking" search space (89.5% literal `*MLB*` tickers, remainder mostly adjacent baseball leagues); does not change any verdict above. Full detail: `exp_output/PHASE0_SURVEY/SURVEY_TABLES.md`.

---

### V-002 — Polymarket US

| Attribute | Value |
|-----------|-------|
| Type | Binary prediction market |
| Regulatory basis | CFTC-regulated (US relaunch December 2025) |
| CA eligible | Yes — CFTC federal jurisdiction |
| ADR status | ADR-0003 ACCEPTED — Phase 6+ secondary venue |
| Activation | 🔲 Phase 7 (T-077 / ACC-0003) |
| API | TBD — Polymarket US REST API (provisioning pending) |
| Pricing structure | Dynamic supply/demand; binary; similar to Kalshi |
| Settlement | $1.00 / $0.00 binary |
| Vig | Est. ~2% (lower than Kalshi — tentative) |
| Series used | NBA player prop markets (availability TBD on US platform) |
| Edge formula | `edge = p̂ - mid_price` (market-priced) |
| Adapter | `PolymarketVenueAdapter` (stub — T-077) |
| implied_prob_method | `market` |
| Primary use | Line shopping (Strategy E); cross-venue complement lock (Strategy C) |
| Open question | NBA player prop market availability + liquidity on US platform |

---

### V-003 — PrizePicks

| Attribute | Value |
|-----------|-------|
| Type | DFS pick'em (fantasy sports) |
| Regulatory basis | Fantasy sports contest (not CFTC) — legal under CA DFS carve-out |
| CA eligible | Yes — DFS legal in California |
| ADR status | Requires new ADR (not covered by ADR-0003) |
| Activation | 🔲 Phase 7+ (new ADR required) |
| API | PrizePicks public API (undocumented; may require partner access) |
| Pricing structure | **Bookmaker-set lines** — static; not market-priced |
| Settlement | Correct pick pays fixed multiplier (standard: 2× for 2-pick power play) |
| Vig | Implicitly embedded in multiplier structure |
| Series used | NBA player points, rebounds, assists props |
| Edge formula | `edge = p̂ - 0.50` (bookmaker targets 50/50 action — larger edges typical) |
| Adapter | `PrizePicksVenueAdapter` (not yet built) |
| implied_prob_method | `bookmaker` |
| Key advantage | Lines less efficient than Kalshi market pricing → larger edges expected |
| Key difference | Fixed multiplier payout vs. binary $0/$1; no YES/NO contract structure |

---

### V-004 — Underdog Fantasy

| Attribute | Value |
|-----------|-------|
| Type | DFS pick'em (fantasy sports) |
| Regulatory basis | Fantasy sports contest — legal under CA DFS carve-out |
| CA eligible | Yes |
| ADR status | Requires new ADR |
| Activation | 🔲 Phase 7+ (new ADR required) |
| Pricing structure | **Bookmaker-set lines** — static |
| Settlement | Fixed multiplier picks |
| Edge formula | `edge = p̂ - 0.50` (bookmaker lines) |
| Adapter | `UnderdogVenueAdapter` (not yet built) |
| implied_prob_method | `bookmaker` |

---

### V-005 — Sleeper

| Attribute | Value |
|-----------|-------|
| Type | DFS pick'em (fantasy sports) |
| Regulatory basis | Fantasy sports contest — legal under CA DFS carve-out |
| CA eligible | Yes |
| ADR status | Requires new ADR |
| Activation | 🔲 Phase 7+ (new ADR required) |
| Pricing structure | **Bookmaker-set lines** — static |
| Edge formula | `edge = p̂ - 0.50` |
| Adapter | `SleeperVenueAdapter` (not yet built) |
| implied_prob_method | `bookmaker` |

---

## Edge Formula by Venue Type

```
Market-priced venues (Kalshi, Polymarket):
  edge = p̂ - mid_price
  where mid_price = (yes_ask + yes_bid) / 2  [dynamic, supply/demand driven]

Bookmaker-set venues (PrizePicks, Underdog, Sleeper):
  edge = p̂ - 0.50
  where 0.50 = bookmaker's target implied probability [static, less efficient]
```

DFS pick'em edges are typically larger because:
1. Lines are set algorithmically once, not continuously repriced by the crowd
2. Retail participant base with no sophisticated quantitative competition
3. No market maker adjusting in real-time

Trade-off: payout structure is fixed-multiplier, not binary $0/$1. Position sizing logic differs.

---

## VenueRouter Configuration

| VENUE_ROUTER_MODE | Behaviour |
|-------------------|-----------|
| `kalshi_only` | Only Kalshi queried (default; safe fallback) |
| `best_price` | All registered adapters queried; best ask per direction returned |

Environment variables required per venue:

| Variable | Venue | Status |
|----------|-------|--------|
| `VENUE_API_KEY` | Kalshi | ✅ Provisioned (ACC-0002 read-only) |
| `POLYMARKET_API_KEY` | Polymarket US | 🔲 T-077 |
| `PRIZEPICKS_API_KEY` | PrizePicks | 🔲 Phase 7+ |
| `UNDERDOG_API_KEY` | Underdog Fantasy | 🔲 Phase 7+ |
| `SLEEPER_API_KEY` | Sleeper | 🔲 Phase 7+ |

---

## Activation Roadmap

| Phase | Venue | Action |
|-------|-------|--------|
| 6 (now) | Kalshi | ✅ Live |
| 7 | Polymarket US | T-077: provision API key; T-078: build adapter + VenueRouter |
| 7 | PrizePicks | New ADR; build PrizePicksVenueAdapter; edge formula update for bookmaker pricing |
| 7 | Underdog Fantasy | New ADR; build UnderdogVenueAdapter |
| 7 | Sleeper | New ADR; build SleeperVenueAdapter |
| 8+ | All | Live order execution via C5 write-capable mode |
