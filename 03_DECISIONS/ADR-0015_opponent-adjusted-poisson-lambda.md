# ADR-0015 — Opponent-Adjusted Poisson λ for T1 Inference

**Status:** ACCEPTED  
**Date:** 2026-06-04 SESSION 30  
**Decisions logged:** true  
**Author:** Claude Code (T-072)  
**Approval required:** DS (Earl Ignacio) sign-off before ACCEPTED  
**Supersedes:** T1 probability estimation in ADR-0014 §T1 — specifically, the λ parameter fed to the Poisson CDF  
**Supplements:** ADR-0014 (per-band decision tree mechanics), ADR-0004 (model class selection)  
**Related:** GG-004 (commercial validation gap), EXP-017 (DIRECTIONAL_NEGATIVE result), EXP-012 (F-040 LR test), T-072

---

## Context

EXP-017 Part B Finals G1 verdict: DIRECTIONAL_NEGATIVE (EV = −$0.162/bet, n=32). The T1 model systematically overestimates scoring probability because its Poisson λ is raw `pts_l10_mean` with no opponent context. The Fox 25+ case was the clearest signal: model predicted 57% (λ=27.5), Kalshi priced 7.5%, actual result 7 pts. OKC's SGA as primary defender was not capturable from raw rolling average. The market priced it correctly.

### Architecture finding (critical — informs this ADR)

The LR model (`p_est_lr`) is computed at inference time, logged to C6, and used by the shadow forecaster. It is **not** the decision-making signal for bet approval or direction. The signal path for all T1 bets is:

```
λ = pts_l10_mean
p_threshold = 1.0 - Poisson.CDF(thresh_int - 1, λ)    ← THIS drives bets
edge = p_threshold - kalshi_mid - half_spread
approve if edge ≥ MIN_EDGE_TO_APPROVE
```

EXP-012 tested adding F-040 (`opp_def_rating_l10_mean`) to the LR feature vector and found Brier delta = −7e-6 (zero improvement). This is consistent with the architecture finding: adding F-040 to a model that is logged but not used for trading changes nothing in actual bet behavior. The correct fix targets λ, not the LR model.

**Corollary: the production LR model retrain (originally part of T-072 scope) is deferred.** Retraining LR with F-040 would require a new ADR per ADR-0004 (frozen model policy), would not change trading behavior, and EXP-012 establishes it adds no Brier improvement. Retrain is out of scope.

---

## Decision

### 1. Opponent-adjusted λ formula

```
adj_λ = pts_l10_mean × clip(opp_def_l10 / LEAGUE_AVG_PTS_ALLOWED, 0.70, 1.30)
```

Where:
- `pts_l10_mean` — 10-game rolling scoring mean for the player (source: EXP-005 cohort row or live nba_api fetch)
- `opp_def_l10` — opponent team's 10-game rolling average points allowed (from TeamStatsStore)
- `LEAGUE_AVG_PTS_ALLOWED = 113.0` — 2025-26 NBA season average; update at season rollover via DECISION_LOG entry (no ADR required for constant refresh)
- Clip bounds `[0.70, 1.30]` — caps adjustment at ±30% to prevent extreme estimates from small-sample team logs or outlier sequences

The `adj_λ` replaces `pts_l10_mean` as the Poisson CDF parameter in PIPE-02 and PIPE-03:

```python
p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, adj_λ)
```

### 2. Opponent extraction from Kalshi ticker

Opponents are extracted at inference time from the Kalshi market ticker (no additional data source required):

```
Ticker: KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20
Segment[1] = "26JUN03NYKSAS" → date(7 chars) + team_a(3) + team_b(3)
Segment[2] = "NYKJBRUNSON11" → player_team(3) + player_id
Opponent = team_b if player_team == team_a else team_a
```

Function: `_parse_ticker_opponent(ticker: str) -> str | None`

Returns `None` if ticker cannot be parsed or player team does not match either matchup team.

### 3. Fallback to raw λ

`adj_λ = pts_l10_mean` (raw, unadjusted) in all of the following cases:
- TeamStatsStore not available at inference time
- Ticker parse returns `None` (malformed ticker, abbreviation mismatch)
- `team_store.get_opp_def_rating()` returns `None` (team not loaded, fewer than 3 prior games)

This ensures backward compatibility: the system continues functioning if the TeamStatsStore build fails or the opponent cannot be resolved.

### 4. TeamStatsStore build and caching

PIPE-02 (`run_pregame.py`) builds TeamStatsStore from 30-team season game logs via `NBAIngestionClient.fetch_team_game_log()` at the start of each pre-game run. The store is cached as `logs/team_stats_cache_YYYYMMDD.json`. PIPE-03 (`run_paper_trade.py`) loads from cache (written ~5 minutes earlier by PIPE-02) and falls back to fresh build if cache is absent.

Season: `DYNAMIC_FETCH_SEASON = "2025-26"`. Season type: regular season only (Phase 1 — playoffs adjustment is a future enhancement; regular season data is sufficient to establish strong/weak defense direction).

### 5. Audit logging

Each forecast record emitted to C6 includes:
- `opp_team` — opponent team abbreviation (`None` if parse failed)
- `opp_adj_lambda` — the computed `adj_λ` used in the Poisson CDF
- Existing fields unchanged: `p_estimate` (Poisson CDF output), `pts_l10_mean`, `p_estimate_lr`

---

## Rationale

| Alternative | Why rejected |
|-------------|-------------|
| Add F-040 to LR model (original T-072) | LR model not used for bet decisions (architecture finding); EXP-012 delta = 7e-6 — zero improvement; retrain requires new ADR per ADR-0004 |
| Use playoff-adjusted team logs | Complexity; regular season data sufficient to establish direction; revisit after EXP-018 |
| Static Finals adjustment constant | Not generalizable; cannot automate to regular season or other sports |
| Change model class (Hypothesis C, PDTP) | Larger scope; ADR-0004 supersession required; correct sequence: fix λ first, test, then decide if model class upgrade warranted |

---

## Validation

EXP-018 is registered to test whether adj_λ fixes DIRECTIONAL_NEGATIVE:
- **Primary metric:** EXP-017 Part B EV/bet on ≥30 games using adj_λ model
- **Acceptance threshold:** EV/bet > 0 (positive net-of-fee edge)
- **Falsification criterion:** If EXP-018 shows EV/bet ≤ 0 on ≥30 games, Hypothesis C (Poisson model class) must be evaluated

---

## Governance implications

- GG-004 status: OPEN. ADR-0015 describes the model correction path. GG-004 closes when EXP-018 confirms positive EV/bet.
- Calibration power floor: APR-0017 ≥66 markets floor remains operative pending EXP-018 δ re-estimate.
- No new ADR required for `LEAGUE_AVG_PTS_ALLOWED` annual refresh — DECISION_LOG entry sufficient.
- If adj_λ model proves insufficient (EXP-018 negative), model class change (Hypothesis C) requires new ADR superseding ADR-0014 §T1 and ADR-0004.
