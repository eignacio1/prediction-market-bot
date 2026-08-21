# SESSION HANDOFF — T-475 (MICRO)

<!-- session-meta
task_id: T-475
tier: MICRO
timestamp: 2026-08-21T02:05:00Z
commit: 9253d9a
one_line_summary: T-475: amended ADR-0054 §5.2 correlation key for non-MLB tickers (reuse T-472 TickerGrammar), registered GG-192
gg_touched: GG-192
adr_touched: ADR-0054
plan_deliverable_moved: no
-->

**Date:** 2026-08-21
**Branch:** session/20260821T015013Z-adr0054-correlation-key (merged to origin/main @ 9253d9a)
**Tier:** MICRO — one deliverable

## What happened

ADR-0054 §5.1's correlation-key claim ("confirmed identical format across 6 families sampled") generalized from an MLB-only sample. Verified the counterexample directly: 158/158 live NBA tickers in `logs/.vps_portfolio_cache_nba.json` are a 13-char `date+away+home` shape with no HHMM segment, versus MLB's 17-char `date+HHMM+away+home`. Amended §5.2 in place (original text preserved, amendment appended) to specify the correlation key as `(game_date, teams_raw)` derived from the already-landed T-472/GG-191 `TickerGrammar` registry (`market_type_registry.py`) — reusing that grammar rather than defining a second one — and to state explicitly that no fallback is permitted anywhere in that path (refusal-only, same discipline as GG-166→GG-170→GG-185's lesson).

Registered GG-192 (OPEN, MEDIUM): the separate §5.1 finding that C4 (`risk.py`) tracks exposure at exactly two granularities — per-bet (`max_single_event_exposure_usd`) and whole-portfolio (`exposure_snapshot()`) — with zero game/family-level grouping. No live consequence at today's one ACTIVE cell; becomes unsound the moment a second correlated cell activates. Confirmed genuinely unregistered before writing (only prior hit was GG-045, a different/market-depth context).

ADR-0054 left at **PROPOSED** throughout — only item (c) is operator-signed; items (a)/(b)/(d) untouched this session.

## Not done (out of scope, Hard Rule 11)

- GG-192's fix (wiring §5.3–5.4's correlation-cap control shape into `risk.py`) — register-and-stop only.
- Stale "Gaps by Arm" summary counts in GOVERNANCE_GAP_LOG.md (pre-existing staleness, not touched).

## Next session

No src/ changed this session — nothing to re-test. GG-192 is available to pick up as its own STANDARD-tier block whenever Phase 3 wiring work starts.
