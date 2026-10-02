# EXP-037 (T-608) D0 — Harvest report (2026-10-02)

**origin/main at fetch:** `1e097e0fa4e0206c7a5ec2fe0dbb9d3c9b541c84` (1e097e0, "Wave 47 / 47.1 D6 h-i ...").
Branch contents are harvested only through this block's own tests; no branch is merged.
Basis: file headers and import graph read on 2026-10-02, plus what the shadow package actually imports. Not a line-by-line audit.

## 1. Reuse / adapt / discard

| File | Verdict | Reason |
|---|---|---|
| `c1_signal_ingestion/nfl_ingestion.py` (557 L) | REUSE (as data source) | nflverse static-asset client (T-526). The shadow refresh pulls the extended schedule and team stats from the same source. Not modified. |
| `c1_signal_ingestion/nfl_team_stats_store.py` (304 L) | REUSE | Recency-weighted off/def EPA with TI-01 strict `game_date < as_of`. Imported by `nfl_pregame_features.py`. Point-in-time safety is the property we need. |
| `c1_signal_ingestion/nfl_espn_results.py` (151 L) | DISCARD for this block | Settlement uses the nflverse final score keyed by (gameday, {home, away}); no second results source needed. Left in place for the paper path. |
| `nfl_exp027_adapter.py` (228 L) | DISCARD | Wraps a moneyline-only LR that was never serialised (fits in memory per its own header). Cannot emit a ladder of strikes; no persisted artifact to hash. Replaced by the frozen, sha-verified `nfl_pregame_v1`. |
| `run_t1_nfl_game_market.py` (495 L) | DISCARD (reference only) | Paper-only run path: imports PaperTrader and RiskEngine. SHADOW forbids those imports (enforced by `test_pregame_shadow_safety.py`). Its market-parsing shape was read, not copied. |
| `run_pregame.py` (439 L) | DISCARD | NBA PIPE-02, 21:30 UTC single window. Wrong sport and wrong cadence; nothing to harvest. |
| `c5_execution/game_market_settlement.py` (228 L) | REUSE | `derive_actual_stat` is imported by `pregame_shadow/nfl_settlement.py`. Pure computation; the paper `settle_position` primitive is untouched. |
| `scripts/exp027_hyp012_nfl_moneyline_backtest.py` (663 L) | DISCARD (incumbent reference) | Pre-registered moneyline LR (HYP-012, UNDERPOWERED). No persisted model, so it cannot be a head-to-head incumbent; stated as a gap. |
| `scripts/nfl_prekickoff_capture.py` (219 L) | DISCARD / DO NOT TOUCH | T-601 capture writer; explicitly outside the cron authorization. We read its output only if present. |

## 2. ADR review

- **ADR-0056 (ACCEPTED):** sport is a first-class `MarketType` attribute; band naming; per-sport epoch inheritance. It governs cell registration. The T1 flips used `promote_cell_status(..., SHADOW, superseding_reference="EXP-037")`. No new ADR is needed for a status flip. RULED_OUT requires `reason` plus `measured_date`.
- **ADR-0062 (ACCEPTED):** NFL/NHL T4 sub-band decomposition. Concerns T4 only; EVENT stays DEFERRED. Authorizes no cell promotion and no kelly. Not engaged by T1/T2/T3 shadow cells. The BOUNDARY §4/§6 conflict is unresolved in that ADR and out of scope here.
- **ADR-0066 (PROPOSED, not accepted):** passing/rushing EPA split candidate. Finding: every Brier difference vs the incumbent spans zero. Not adopted. Its evidence also bounds expectations: neither EXP-027 variant beat the 2026 closing price at n=48.

## 3. `git cherry -v origin/main <branch>` (`+` = not on main)

| Branch | Unmerged commits |
|---|---|
| `session/20260907T234557Z-nfl-c1-ingestion` | 3: 1af43dc, c728767, 1381fe4 (session-end close-out / handoff artifacts only; code is on main) |
| `session/20260907T234611Z-nfl-game-market-settlement` | 1: 0b2870f (close-out, truncated at budget) |
| `session/20260929T050111Z-exp027-epa-splits` | 0 (empty) |
| `session/20260929T052119Z-nfl-accrual-path` | 0 (empty) |
| `session/20260930T050102Z-nfl-ingestion-widen` | 0 (empty) |
| `session/20260909T153928Z-gg255-mlb-t1-game-market-run-script` (D6 harvest) | 4: 3619ec3 (kalshi_client MLB series, not ours to modify), ee5066f (`run_t1_mlb_game_market.py` + tests), 25c081f, 262c92a (close-out docs) |

Note: the brief's "five branches" list was not in my context; I used the NFL set above and added the gg255 MLB branch. Re-run if a different five were intended.
Disposition: the NFL branches carry no unmerged code. gg255's `run_t1_mlb_game_market.py` is paper-path (PaperTrader/RiskEngine), so it follows the same reference-only rule as its NFL twin in section 1.

## 4. Gaps (for 47.1 / Wave 48 to register; nothing written to GOVERNANCE_GAP_LOG.md)
- The EXP-027 incumbent has no persisted artifact and is moneyline-only: no head-to-head is possible.
- The brief's five-branch list was not recoverable from session context.
