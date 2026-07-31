# Market Universe Survey Spec + Venue Compliance Validation (Phase 0)

**Status:** DRAFT — spec only, no code, no live change.
**Date:** 2026-07-30
**Purpose:** Phase 0 precondition for the team-level market expansion (ML / run line / totals). Nothing in Phases 1–4 starts until § 2's survey artifact exists.
**Why this exists:** the market universe has never been enumerated. `kalshi_client.py:115` records `SERIES_MLB_PLAYER_HITS = "KXMLBHIT"  # Confirmed 2026-06-23 via GET /series` — a single call made to confirm a ticker already assumed, not to ask what the venue lists. This document closes that gap and validates venue compliance at the same time.

---

## 1. External confirmation (completed 2026-07-30 — desk research, NOT the API survey)

**Kalshi does list the three target market families for MLB.** Confirmed via Kalshi's public sports catalog and third-party coverage: outright game winners, run-line spreads, game totals, team run totals, and season win totals, alongside the player-prop milestones already traded. This validates the premise of the expansion but is **not a substitute for § 2** — series tickers, threshold structures, resolution sources, and depth remain unverified and can only come from the authenticated API.

**Automated trading is permitted** under Kalshi's terms, subject to rate limits and conduct rules. Confirmed constraints, all currently absent from this repo:

| Constraint | Value | Repo status |
|---|---|---|
| Position limit | **$25,000 per contract** (Rulebook 5.14(a)) | **Not recorded anywhere.** Does not bind today — `_HARD_LIMITS["max_single_event_exposure_usd"]=500.0` is 50× inside it — but it is the true external ceiling and belongs in `_HARD_LIMITS`' derivation notes alongside GG-045's depth ceiling. |
| Rate limits | Token-bucket, billed separately for Read and Write. Most requests cost **10 tokens**. Basic tier = **200 read / 100 write tokens/sec** → ~20 reads/sec, ~10 writes/sec. Advanced 300/300, Premier 1,000, Paragon 2,000, Prime 4,000. | **Tier unknown.** Never recorded, never checked. |
| Burst headroom | Write bucket holds 2 seconds of budget — **except Basic, which holds 1 second with no accumulated headroom** | Not modeled. |
| Batch endpoints | **Do not save tokens** — 25 orders costs 25 × 10 = 250 | Not modeled. |
| 429 handling | No `Retry-After` or `X-RateLimit-*` headers returned; exponential backoff required | **Implemented** — `kalshi_client.py:355,388` backs off on 429/503. ✓ |
| Live limit introspection | `GET /account/limits` returns live refill rates and capacities | **Never called.** |
| Conduct | Wash trades, money passes, self-matching, spoofing, front-running prohibited | **See § 3 — live finding.** |

**Rate-limit implication for this build.** T4 currently evaluates every 45–90s across all live games. Adding three team-level market families multiplies read volume per cycle. At Basic tier (~20 reads/sec) that is probably still fine, but *it has never been measured*, and the tier has never been confirmed. § 2 must establish both.

---

## 2. The survey — what to actually run

Requires an authenticated session from the datacenter IP (VENUE_REGISTRY: CloudFront WAF blocks home/work ISP). Run on the VPS. Read-only; no orders.

**2.1 — Enumerate.** `GET /series` unfiltered. Dump every series ticker, title, category, and status to a committed artifact. Do not filter to what you expect to find. This is the step that was skipped.

**2.2 — For every MLB series returned, record:**
series ticker · market family (winner / run line / total / team total / win total / prop) · threshold or strike structure · YES/NO semantics and what resolves YES · settlement source and resolution lag · typical event count per game-day · open/close times relative to first pitch.

**2.3 — Depth, per family.** For a representative sample of ≥20 live markets per family, capture the orderbook (`GET /markets/{ticker}/orderbook`): top-of-book size both sides, cumulative size within 5¢ of mid, and observed half-spread. **This is the GG-045 measurement that has never been taken for any family, including the one being traded today.** Output: a depth table by family, so the capital ceiling is a measured number rather than the "$500–$2,000 estimated" figure currently carried in CLAUDE.md.

**2.4 — Tier + limits.** `GET /account/limits`. Record tier, read/write budgets, capacities. Record it in `VENUE_REGISTRY.md`.

**2.5 — Fee structure per family.** Kalshi's fee is price-dependent; the props path already carries `fee_per_contract` / `fee_net_edge`. Confirm whether the same schedule applies to game markets, since edge thresholds are net-of-fee.

**2.6 — Deliverable.** `02_ARCHITECTURE_DESIGN/MARKET_UNIVERSE_SURVEY_2026-XX-XX.md` — the raw enumeration plus the four tables (families, thresholds, depth, fees), committed. Update `VENUE_REGISTRY.md` with tier, position limit, and measured depth.

**2.7 — Gate.** If measured depth for a family is below roughly 10× intended per-bet stake, that family does not proceed past Phase 2 regardless of modeled edge. Depth is a hard ceiling that no amount of model quality overcomes (GG-045).

---

## 3. LIVE COMPLIANCE FINDING — offsetting same-contract positions

**Measured on the T4M-PROJ ledger, 2026-07-30. This is not hypothetical.**

- **161 tickers** have been held in **both YES and NO** within the T4 book.
- **All 161 are simultaneously open** — zero sequential (close-then-reverse). Verified by entry/resolution timestamp overlap. Example: `KXMLBHIT-26JUL051430STLCHC-CHCPCROWARMSTRONG4-2`, NO entered 18:37:30Z, YES entered 19:20:26Z, both held to resolution ~06:48Z.
- A further **35 tickers** carry opposite directions across the T1 and T4 books — same exchange account, different internal pools.
- Closed locked pairs: **141 tickers / 374 legs**, combined **−$0.13 on $178.76 stake (−0.07% ROI)**.

**Two separate problems, both real.**

**(a) Compliance.** Holding YES and NO simultaneously on the same contract from one account is economically a wash — the pair pays exactly $1.00 regardless of outcome, so the only economic content is the premium spread plus fees. That is the pattern wash-trade and self-match conduct rules exist to catch. At paper stage it is harmless and there is no intent to manipulate — the model simply re-evaluated and took the other side without closing the first. **At live capital on a CFTC-regulated DCM it is an exposure**, and it must have a documented policy and a hard preventive control before G6, not after. Note `c5_execution/complement_lock_scanner.py` exists but addresses *cross-venue* complement locks (Strategy C arbitrage), not intra-account same-contract offsetting — verify before assuming coverage.

**(b) Measurement contamination — affects the run currently in flight.** 374 of 2,015 T4 legs (**18.6%**) are locked pairs whose combined outcome is deterministic. They carry **zero information about edge** while consuming 20% of the book's stake and inflating `n`. Any `clean_n`, `n*`, or per-bet-edge figure computed over a cohort containing locked pairs is diluted by a structurally uninformative 19%.

**Required actions:**

1. **Immediate, into the live T4 measurement reactivation:** add same-ticker opposite-direction suppression — do not open a position on a ticker where an offsetting position is already open; close-and-reverse or hold, per an explicit rule. This is a small guard and it is cheaper to add now than to re-accrue the cohort later.
2. **Pre-register** locked pairs as excluded from the measurement cohort, alongside the price and threshold strata already agreed. Decide now, before the data exists.
3. **Register as a governance gap** — this is a live conduct exposure and a measurement defect, currently unregistered.
4. Scope forward: the team-level families make this materially worse. ML, run line, and totals on the same game are economically correlated, not independent. A policy covering *correlated offsetting exposure across families*, not just identical-ticker offsetting, is required before Phase 4.

---

## 4. Assumptions | Risks | Validation | Confidence

**Assumptions.** § 1 rests on Kalshi's public documentation and catalog as of 2026-07-30; the rate-limit table is quoted directly from `docs.kalshi.com/getting_started/rate_limits`. Position limit is quoted from the CFTC-filed rulebook and may have been amended in a later version — re-verify against the current DCM rulebook before citing in an ADR. The § 3 ledger analysis is exact (direct timestamp overlap on the real ledger), not modeled.

**Key risks.** Depth may prove insufficient for one or more families, killing the expansion after Phase 0 — that is the correct outcome and the reason this phase is first. Tier may be Basic with no burst headroom, constraining T4 cadence once families multiply. The § 3 finding may extend to the props book in ways not yet measured (T1's book shows zero intra-book offsetting, but the 35 cross-book cases are unexamined).

**Validation checks.** (1) Re-run the § 3 ledger query after the T4 reactivation deploys and confirm the suppression guard drives new locked pairs to zero. (2) Confirm the position limit against the current rulebook version, not the filing found here. (3) Cross-check measured depth against the "$500–$2,000" estimate CLAUDE.md carries and correct that figure.

**Confidence.** Kalshi lists the three families — High. Rate limits and tier structure — High (primary source). Position limit $25k — Medium (rulebook version uncertainty). § 3 offsetting-position finding — High (exact ledger computation). Depth adequacy — Unknown, and that is the point of § 2.

---

**Sources:** [Kalshi rate limits and tiers](https://docs.kalshi.com/getting_started/rate_limits) · [KalshiEX LLC Rulebook v1.26](https://kalshi-public-docs.s3.amazonaws.com/regulatory/rulebook/Kalshi%20DCM%20Rulebook%201.26.pdf) · [Rulebook amendment re position limits (CFTC filing)](https://www.cftc.gov/sites/default/files/filings/orgrules/23/02/rule022123kexdcm002.pdf) · [Kalshi sports props catalog](https://kalshi.com/category/sports/all-sports/all/props) · [Kalshi Member Agreement](https://kalshi.com/docs/kalshi-member-agreement.pdf)
