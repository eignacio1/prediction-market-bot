> **HISTORICAL — archived 2026-10-09.** This was the body of `.claude/commands/ctx.md` until the strategic window's forest pass replaced it with a pointer-based version. It describes the project as of late May 2026. Do not use it for current state.

# /ctx — Full Project Context Restore

You are the analytical copilot for the **Prediction Market Trading Bot** project. Read this entire block before doing anything. Confirm "Context loaded." and wait for instructions.

---

## Project Identity

| Field | Value |
|-------|-------|
| Project | Prediction Market Trading Bot |
| Operator | Earl Ignacio (sole operator across all roles) |
| Framework | Compass OS (ADR-0001) |
| Strategy | Forecast-only (ADR-0002); arb/ = REFERENCE ONLY until APR-0010 |
| Capital status | NO LIVE CAPITAL — paper trading only until G6 |
| Current phase | **Phase 6/7 ACTIVE — paper trading live; Phase 7 infrastructure fully built** |
| Last gate closed | G5 — APR-0007 ACCEPTED 2026-05-28 |
| Production model | v1-28483b21 — 78 features (31 quant + 47 qual); sklearn 1.8.0; `models/prod_model.joblib` |
| Tests | **533/533 passing** |

---

## Gate History

| Gate | Status | Date | Approval |
|------|--------|------|----------|
| G0–G5 | ✅ ALL CLOSED | 2026-05-22 to 2026-05-28 | APR-0002 through APR-0013 |
| G6 Live Capital | 🟡 IN PROGRESS | — | 30 resolved paper bets + positive P&L required (APR-0016) |

---

## ABSOLUTE INVARIANTS (read before every action)

1. arb/ = REFERENCE ONLY (APR-0010 required before any use)
2. ADRs immutable — superseding ADR for any change
3. No real capital until G6 (ADR-0005 + APR-0008/0009)
4. No automated retraining — frozen model; new ADR required
5. NFR-05: zero hardcoded secrets
6. NFR-03: kill switch ≤60s, no bypass
7. BOT_C4_ACTIVE must NOT be set in ENV-01 or ENV-02
8. **G6 gate = 30 resolved paper bets** (APR-0016, signed 2026-05-29 — NOT 50; revised per seasonal constraint)
9. Strategic decisions must be captured in DECISION_LOG + APPROVALS_REGISTER before session end

---

## ADRs (IMMUTABLE once accepted)

| ADR | Decision |
|-----|----------|
| ADR-0001 | Compass OS governance |
| ADR-0002 | Forecast-only; arb/ reference-only |
| ADR-0003 | Kalshi primary (CFTC-DCM, all 50 states); Polymarket US Phase 6+ secondary |
| ADR-0004 | LR+Platt confirmed; TEST Brier +0.0084/ECE 0.0247 |
| ADR-0005 | PENDING G6 — live capital authorization |

---

## Strategic Context (as of 2026-05-29)

**NBA Season Timeline:** NBA Finals end ~2026-06-22. NBA goes dark until ~2026-10 (2026-27 preseason).  
**Dark Period Plan:** Use 2026-06-22 to 2026-10 to build: Polymarket activation (T-077), DS-04 qualitative source (T-073), ADR-0005 live capital draft, Phase 8 prep. Do NOT treat as idle time.  
**G6 Threshold Decision (APR-0016):** Revised from 50 → 30 resolved paper bets. Seasonally bounded. If not reached by Finals end, accumulation window extends to first 30 days of 2026-27 regular season.  
**All 9 hypotheses resolved.** EXP-016 HYP-009 CONFIRMED: playoff paper bets count as full-confidence G6 evidence.

---

## Component Pipeline

```
nba_api → C1 → C2 (78 feat, FEATURE_VERSION 1.2.0) → C3 (LR+Platt) → C4 (risk/kill) → C5 (Kalshi/VenueRouter)
                                                                                        → C6 (audit JSONL)
                                                                                        → C7 (drift monitor)
                                                                                        → C8 (dashboard)
```

Kill switch SLA: ≤60ms tested (0.340ms actual). **533/533 tests green.**

Phase 7 infrastructure (all built, not yet activated for live capital):
- `c5_execution/market_mapper.py` — cross-venue player name normalization
- `c5_execution/complement_lock_scanner.py` — lock detection (APR-0010 gates execution)
- `c5_execution/venue_router.py` — VenueRouter (kalshi_only now; best_price when Polymarket live)
- `execution_bands_orchestrator.py` — MultiBandOrchestrator; T3>T2>T1 priority rules
- `c3_forecasting/scoring_distribution.py` — ScoringDistributionModel (NB/Poisson)

---

## Production Model

```
model_version: v1-28483b21
feature_count: 78 (31 quant + 47 qual)
FEATURE_VERSION: 1.2.0 (NOTE: 1.3.0 infrastructure built but FALSIFIED by EXP-012; stays 1.2.0)
quant: L10 rolling stats + flags + season means
qual:  prf_w01–prf_w15 (PRF weights) + mod_01–mod_32 (qualitative modifiers)
path:  models/prod_model.joblib + models/prod_model_meta.json
trained: 2026-05-29T01:52:58Z on 12,748 rows (5 seasons 2021-26); retrained natively on VPS
sklearn: 1.8.0 (VPS Python 3.12; must match)
Brier: 0.2461 (+0.0039 vs null) | ECE 0.0342 | AUC 0.5765 | EV +$0.0958/bet
```

---

## All Experiment Results

| Exp | Result | Verdict | Notes |
|-----|--------|---------|-------|
| EXP-001 | Brier Δ +0.0056, ECE 0.0345 | ✅ | G4 window 1 |
| EXP-002 | Brier Δ +0.0049, ECE 0.0289 | ✅ | G4 window 2 |
| EXP-003 | Brier Δ +0.0026, ECE 0.0369 | ✅ | G4 window 3 |
| EXP-004 | EV +$0.0855/bet, 59% win | HYP-003 ✅ CONFIRMED | vs Kalshi vig |
| EXP-005 | Brier Δ +0.0024, ECE 0.0456 | ✅ | 5-season refresh; prod candidate |
| EXP-006 | Δ=0.0000 | expected null | QS-001 temporal baseline |
| EXP-007 | Brier Δ +0.0017 | positive signal | QS-002 backdated QTI-03 |
| EXP-008 | negligible | — | PRF one-hot; LR insensitive to ordinality |
| EXP-009 | Δ=−0.0004 | — | L3 amplification; LR cannot exploit |
| EXP-010 | EV +$0.0958/bet, 61.1% win | ✅ | EV re-est with refreshed model + live vig |
| EXP-011 | HGBC Δ=−0.0008 | LR RETAINED | below ADR-0004 threshold 0.003 |
| EXP-012 | Δ Brier = 0.0000 | HYP-006 🔴 FALSIFIED | opp_def_rating + is_home_game no signal; FEATURE_VERSION stays 1.2.0 |
| EXP-013 | NB Brier 0.2671 vs LR 0.2461 | HYP-007 🔴 FALSIFIED | NB useful for multi-line pricing only |
| EXP-014 | +7.8% max EV | ✅ | line shopping; ~51–104 locks/season |
| EXP-015 | T3 EV ratio 0.84 | HYP-008 🔴 FALSIFIED | T3 = FADE gate only, not confidence booster |
| EXP-016 | Δ Brier = −0.0010 | HYP-009 ✅ CONFIRMED | playoff paper bets = full-confidence G6 evidence |

---

## Key Source Files

```
src/prediction_market_bot/
  c1_signal_ingestion/ingestion.py          NBAIngestionClient
  c1_signal_ingestion/team_stats_store.py   TeamStatsStore (opp def rating; F-039/040 built but dormant)
  c2_feature_store/features.py              FeatureStore (quant, FEATURE_VERSION 1.2.0)
  c2_feature_store/qualitative_store.py     QualFeatureStore
  c2_feature_store/qualitative_amplifier.py PRF + modifiers
  c3_forecasting/forecaster.py              ModelForecaster
  c3_forecasting/scoring_distribution.py    ScoringDistributionModel (NB/Poisson)
  c4_risk_engine/risk.py                    RiskEngine + kill switch + MIN_BET_USD=$10 floor
  c5_execution/kalshi_client.py             KalshiMarketClient (read-only ENV-02)
  c5_execution/venue_adapter.py             VenueAdapter protocol + KalshiVenueAdapter
  c5_execution/venue_router.py              VenueRouter (kalshi_only → best_price when Polymarket live)
  c5_execution/market_mapper.py             normalize_player_name + PlayerMarketKey + group_by_key
  c5_execution/complement_lock_scanner.py   LockOpportunity + ComplementLockScanner (detection-only)
  execution_bands.py                        ExecutionBand T1–T5 + BandConfig
  execution_bands_orchestrator.py           MultiBandOrchestrator; T3>T2>T1 priority; batch_decide()
  run_pregame.py                            PIPE-02 live daily inference
  run_paper_trade.py                        PIPE-03 paper trading
  run_resolve.py                            PIPE-03R resolution-only (06:00 UTC)
  run_t2_sameday.py                         PIPE-05 T2 injury overlay skeleton
  run_t3_pretip.py                          PIPE-06 T3 momentum scan skeleton
  cohort.py                                 Player cohort registry (v2 ~80 players)
  train_and_save_model.py                   Model serialization
02_ARCHITECTURE_DESIGN/STRATEGY_OVERVIEW.md  All 11 strategies A–K + T1–T5 execution bands
02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md    T1–T5 band design
02_ARCHITECTURE_DESIGN/VENUE_REGISTRY.md     V-001–V-005 CA-eligible venues
models/prod_model.joblib + prod_model_meta.json
deploy/cron.conf  env.template  healthcheck.sh  setup.sh  DEPLOYMENT_GUIDE.md
```

---

## VPS / Cron

```
VPS: 157.230.91.33 — DigitalOcean NYC3, Ubuntu 24.04, Python 3.12, sklearn 1.8.0
SSH: ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33
GitHub: github.com/eignacio1/prediction-market-bot (private); deploy key on VPS
Environment: ENV-02 (paper; read-only Kalshi key; BOT_C4_ACTIVE must NOT be set)

Active cron:
  21:00 UTC — Health check (deploy/healthcheck.sh)
  21:30 UTC — PIPE-02 inference (run_pregame.py)
  22:00 UTC — PIPE-03 early (paper bets, 7pm ET games)
  01:30 UTC — PIPE-03 late (paper bets, 9pm+ ET games)
  06:00 UTC — PIPE-03R resolve-only (run_resolve.py)
  14:00 UTC Mon — Model freshness check (deploy/check_model_freshness.py)

Pending (activate when Polymarket live):
  17:00 UTC — PIPE-05 T2 injury overlay
  */15 20-23,0-3 * * * — PIPE-06 T3 momentum scan

VENUE_ROUTER_MODE: kalshi_only (default) → best_price when POLYMARKET_API_KEY set (T-077)
Paper bankroll: $1,000 — logs/paper_portfolio.json on VPS
Connectivity: any non-work network passes WAF (work ISP blocked by strict outbound policy)
```

---

## Next Tasks (Priority Order)

| Task | Priority | Status | Notes |
|------|----------|--------|-------|
| T-070: Accumulate 30 paper bets → G6 gate | HIGH | 🟡 0/30 | Monitor VPS logs/paper_portfolio.json; dual-window cron active |
| T-077: Polymarket KYC + API key | HIGH | 🔲 Operator action | polymarket.com → KYC → set POLYMARKET_API_KEY in .env → activation runbook |
| T-073: DS-04 qualitative source registration | MED | 🔲 | First new qual source beyond PAM; operator decision |
| T-081: APR-0010 DS sign-off | MED | 🔲 Operator action | Unlocks complement lock scanner execution (Strategy C) |
| T-062: Context Pack Phase 6 | LOW | 🔲 | CP-2026-05-29_phase6-active.md |
| T-082: Phase 7 context pack | LOW | 🔲 | Phase 7 infrastructure frozen; pack it |
| T-061: ADR-0005 live capital authorization | LOW | 🔲 | After 30 paper bets + positive P&L |

**Dark period build queue (for NBA offseason 2026-06-22 to 2026-10):**
- Polymarket activation end-to-end (if T-077 operator-gated)
- DS-04 qualitative source (T-073)
- ADR-0005 first draft
- Phase 8 preparation

---

## Blocked Items

| Task | Blocked By |
|------|-----------|
| T-077 Polymarket activation | polymarket.com KYC (1–3 days operator action) |
| T-081 complement lock execution | APR-0010 DS sign-off |
| T-061 ADR-0005 live capital | 30 resolved paper bets + positive P&L |

---

## Work Style

Optimize for precision and defensibility. Read MEMORY_BANK.md and TODO_NEXT.md at session start. Update both before ending any session. **Capture strategic decisions in DECISION_LOG + APPROVALS_REGISTER — not just code changes.** Session handoffs must include a "Strategic Decisions This Session" section.
