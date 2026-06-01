# Venue Registry — CA-Eligible Prediction Markets

**Purpose:** Register all target venues for this system — mechanics, regulatory basis, CA eligibility, pricing structure, edge formula, and activation status.
**Owner (role):** Architecture Owner (AO)
**Status:** CANONICAL (2026-05-29)
**Last reviewed:** 2026-05-29 (initial build — Phase 6 idle period)
**Next review:** On any new venue activated; on API change; on regulatory status change
**Staleness triggers:** Venue added or removed; regulatory change; API version change; ADR update
**Upstream links:** STRATEGY_OVERVIEW.md; ADR-0003 (venue selection); INTERFACES_CONTRACTS.md
**Downstream links:** venue_adapter.py (implementation); venue_router.py (routing); ENVIRONMENTS.md (API keys)
**Decision references:** ADR-0002 (forecast-only); ADR-0003 (Kalshi primary; Polymarket secondary)
**Confidence:** 8/10
**Decisions logged:** false — V-001–V-005 venue prioritization order, activation roadmap sequencing, and edge formula choices per venue type not yet in DECISION_LOG.md. See T-096 in TODO_NEXT.md.

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
| Vig | ~3% confirmed (EXP-010: vig = 0.030) |
| Series used | KXNBAPTS — NBA Player Points |
| Edge formula | `edge = p̂ - mid_price` (market-priced) |
| Adapter | `KalshiVenueAdapter` (`c5_execution/venue_adapter.py`) |
| implied_prob_method | `market` |
| Connectivity | Datacenter IP required (CloudFront WAF blocks home/work ISP) |

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
