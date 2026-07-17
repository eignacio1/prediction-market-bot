# APR-0029 — GG-045: Kalshi Market-Depth Capital Ceiling — Decision Request (PROPOSED)

**Status:** PROPOSED — awaiting DS sign-off Earl Ignacio. This is a mechanism proposal from prep/data-collection work, not a live code change (Hard Rule 3 — this touches C4 risk-engine position sizing).
**Date:** 2026-07-17
**Session:** T-377, isolated worktree `session/20260717T051845Z-gg045-depth-analysis`, drafted per explicit task instruction: derive a proposed depth-aware max-stake mechanism as a recommendation to Earl, not something to wire into C4 without his sign-off.
**Operator:** Earl Ignacio
**Scope of this request:** GG-045 only (Kalshi order-book depth vs. maximum effective position size). Does not propose any change to Kelly fraction calibration (ADR-0040), `MIN_EDGE_TO_APPROVE`, `DEFAULT_KELLY_FRACTION`, or any band's `kelly_fraction`. Does not touch GG-020, GG-044, GG-046, GG-059, GG-060, GG-072, GG-091, GG-105, or any NBA-tagged work (explicit exclusion this session). Does not modify `scripts/query_orderbook_depth.py` (T-127/KI-023, NBA-scoped) — a separate MLB-scoped script was written instead.
**Supersedes / relates:** GG-045 (this request's governing gap, OPEN, LOW urgency, updated this session with the empirical finding below), GG-041 (prior NBA depth-pull attempt that hit an all-zero pregame read — this session independently reproduced the same pattern for MLB), DECISION_LOG.md 2026-05-29 RETROACTIVE entry (the `$500/bet` `max_single_event_exposure_usd` cap, already liquidity-motivated in its stated rationale but set without empirical depth data).

---

## Context

**The existing $500/bet hard cap (`risk.py` `_HARD_LIMITS["max_single_event_exposure_usd"]`) was reasoned, in the 2026-05-29 RETROACTIVE DECISION_LOG.md entry, as preventing "single-event market impact at Kalshi's thin liquidity" — but no empirical depth measurement has ever backed that number.** GG-045 registered this gap on 2026-06-26 (SESSION 94); it has remained an open, low-urgency watch item because current paper bankroll ($1,000) keeps position sizes small regardless. This session began the empirical groundwork.

**Real paper position sizes, pulled directly from the VPS ledgers (`paper_portfolio_mlb.json`, `paper_portfolio_mlb_t4.json`), for comparison:**

| Band | n (closed positions) | min | max | mean | median |
|---|---|---|---|---|---|
| T1 (MLB) | 259 | $1.05 | $43.56 | $10.16 | $8.54 |
| T2 (MLB) | 2 | $8.11 | $21.27 | $14.69 | $14.69 |
| T4M-PROJ | 910 | $0.005 | $0.965 | $0.53 | $0.55 |

All real position sizes observed are 1–2 orders of magnitude below the $500 hard cap, and below even the low end of GG-045's own unverified $500–$2,000/market depth estimate. This confirms GG-045's own "LOW urgency now" framing — at current bankroll, depth is very unlikely to be binding today. The open question is what happens at scale (G8+, larger bankroll), which is what this request's proposed mechanism is for.

**Depth data collection — real attempt, partial result:**

Built `scripts/query_orderbook_depth_mlb.py` (MLB-scoped analog of the NBA `scripts/query_orderbook_depth.py` from T-127/KI-023, written as a new file rather than modifying the NBA original). Ran it live against the production Kalshi API (read-only, unauthenticated market-data endpoint) at 2026-07-17T05:27 UTC against 30 open `KXMLBHIT` markets spanning 5+ distinct games in the day's slate (STL@AZ, WSH@ATH, SF@SEA, BAL@HOU, and others).

**Result: `combined_depth_usd = $0.00` on all 30 markets sampled.** At sample time, no MLB game was live anywhere (confirmed via ESPN scoreboard: prior game PHI@NYM had gone final 4.5h earlier; the day's next game did not start for another ~12h). **This reproduces the exact GG-041 dead-end** (an earlier NBA KXNBAPTS depth pull, run pre-market before Finals markets opened, also returned all-zero depth). Two independent instances across two sports now support the same operational conclusion: Kalshi player-prop orderbooks carry no resting liquidity until close to/during the live game window. Raw audit trail: `logs/orderbook_depth_mlb_20260717_052732.json` (T-377 worktree).

**This session did not obtain nonzero real depth numbers.** The concrete next step — a re-run of `query_orderbook_depth_mlb.py --all` during an actual live MLB window (any ticker whose game is in ESPN "in" state, not "pre") — is deferred, not yet executed. This request proposes the *mechanism* now, to be numerically calibrated once that data exists.

## Decision requested

This request proposes — but does **not** enact — the following:

**Proposed D1 — Add a depth-aware position-size cap to C4, expressed as a formula, not a fixed dollar figure:**

```python
# Proposed addition to risk.py's sizing path (NOT implemented — mechanism only):
#
# max_stake = min(
#     kelly_size,                              # existing fractional-Kelly output
#     _HARD_LIMITS["max_single_event_exposure_usd"],  # existing $500 flat cap, unchanged
#     DEPTH_IMPACT_PCT * combined_depth_usd,   # NEW: depth-derived cap
# )
#
# DEPTH_IMPACT_PCT proposed at 0.05 (5% of visible combined depth), inherited from the
# existing precedent in query_orderbook_depth.py's DEPTH_IMPACT_THRESHOLD_PCT (T-127/
# KI-023) — itself not yet empirically validated for either sport. Flagged as an
# assumption to revisit once live-window depth data exists, not a derived constant.
```

This does not replace the flat $500 cap — it adds a second, market-specific ceiling that only binds when a market's real depth is thin enough that 5% of it falls below $500 (i.e., depth under $10,000/market). Whether that threshold is ever crossed at current or near-term bankroll is exactly the open empirical question this session could not yet answer.

**Proposed D2 — Register the live-window timing constraint as a standing operational rule for this gap**, so future attempts at GG-045 data collection do not repeat the same pregame-zero dead-end a third time: any orderbook depth pull for GG-045 must be run against a ticker whose underlying game is confirmed live (ESPN scoreboard `state == "in"`, or equivalent), never pre-market or post-resolution. This is now documented in `query_orderbook_depth_mlb.py`'s own docstring and in GG-045's updated `GOVERNANCE_GAP_LOG.md` entry (this session).

**Proposed D3 (explicitly deferred, not decided here):** whether `DEPTH_IMPACT_PCT` should be 5% (carried over from the NBA precedent) or a different value is itself an open question this request does not resolve — it requires either empirical calibration against real fill-price degradation data (not available) or a deliberate operator judgment call independent of any single data point. Flagged for future work, not decided by this memo.

## Decision — [awaiting sign-off]

*(unfilled — Status: PROPOSED)*

## Evidence / reproducibility

- Depth-pull script: `scripts/query_orderbook_depth_mlb.py` (T-377, new, MLB-scoped, does not modify the NBA original).
- Raw audit output: `logs/orderbook_depth_mlb_20260717_052732.json` (30 markets, all-zero depth, pregame sample).
- Position-size distribution: pulled live from VPS `logs/paper_portfolio_mlb.json` (T1/T2 closed_positions) and `logs/t4_mlb_resolved_ledger.jsonl` (T4M-PROJ), 2026-07-17.
- Governing gap: GG-045, `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (updated this session with the empirical pregame-zero finding).
- Structural template: mirrors ADR-0045 / APR-0028's D1/D2 Decision-Request shape.
- Precedent for the timing constraint: GG-041 (NBA KXNBAPTS pregame-zero depth pull, T-127/KI-023).

## Open items

- **Not yet resolved — the core empirical gap remains open.** A live-window depth pull (re-run `query_orderbook_depth_mlb.py --all` while an MLB game is actually in progress, ideally across several games/times-of-day) has not been executed. This is the concrete next step before `DEPTH_IMPACT_PCT` or any real dollar ceiling can be calibrated from data rather than carried over from the NBA precedent.
- Proposed D1's formula is a mechanism sketch, not proposed for implementation until (a) live depth data exists and (b) Earl signs off per Hard Rule 3 — no code change is requested by this memo.
- Whether 5+ games' worth of live-window sampling is sufficient, or whether depth needs to be tracked across the full pregame→live→post-resolution lifecycle of a single market to be useful, is not addressed here.
