# Dark Period Build Plan — June–October 2026

**Purpose:** Operational plan for the NBA offseason gap between Finals end (~2026-06-13) and NBA 26-27 regular season tip-off (~2026-10-20). Not idle time — structured build window with commercial validation work and infrastructure hardening.  
**Owner (role):** Director/Sponsor (DS)  
**Ratified:** 2026-06-11 SESSION 51  
**Status:** ACTIVE  
**Decisions logged:** true

---

## Why This Window Matters

The dark period is not a pause. Three load-bearing things must happen before the 2026-27 regular season starts:

1. **Commercial validation infrastructure:** EXP-017 transitions to MLB/regular-season scale per ADR-0024. The dark period is when MLB paper trading infrastructure is built and EXP-017 MLB runs.
2. **Model refresh:** Model v1-28483b21 was trained through 2026-05. It will be 5+ months stale at 2026-27 tip-off. Retraining by 2026-10-15 is required (per 2026-05-29 DECISION_LOG entry; T-072 elevated to required).
3. **Governance hardening:** T-153 (fill-realism haircut), T-156 (ADR-0012 amendment), T-159 (state-machine invariant tests) must complete before G6 evidence is evaluated. These need G4/G5 data that is now available.

---

## Timeline

| Period | Phase | Focus |
|--------|-------|-------|
| June 13–30 | Phase 1 — Post-Finals Close | Resolve G5, run post-game experiments, governance debt |
| July 2026 | Phase 2 — Infrastructure Sprint | Model retrain, T2 injury source, Polymarket, ADR-0005 |
| June 24 – September 2026 | Phase 3 — MLB Commercial Validation | **LIVE as of 2026-06-24** (started 5-6 weeks ahead of original August plan). MLB C1–C3 + PIPE-05 stack complete (T-187 A–H). EXP-017 MLB run after ≥20 closed positions. ADR-0024 Tier 1 check at n≥150. |
| October 2026 | Phase 4 — Pre-Season | Final integration, G6 evidence review, live capital prep |

---

## Phase 1 — Post-Finals Close (June 13–30)

**Gate:** G5 must resolve cleanly. GHA auto-resolve fires at 05:30 UTC June 14.

| Task | Priority | Notes |
|------|----------|-------|
| G5 post-game resolve (automatic via GHA) | P0 | GHA `post_game_resolve.yml` cron fires June 14 05:30 UTC. No manual action required unless GHA fails. |
| EXP-017B + EXP-018 rerun on G5 data | P0 | Mac cron `post_game_g4_resolve.sh` runs EXP-017B + EXP-018 post-G5. Review results — final NBA Finals commercial validation snapshot. |
| GG-014 status snapshot | P0 | Pull G5 batch integrity report from VPS logs. Document final T-164 failure rate. This is the last production data before dark period — critical for confirming T-164's effectiveness before 2026-27. |
| T-153: Fill-realism haircut on all G4/G5 P&L | P1 | G4/G5 spread data (`spread_observations.jsonl`) now available. Haircut T1 + T4 paper P&L used as G6 evidence. All G6 Tier 2 P&L reports carry "unhaircut paper fills" caveat until this is complete. |
| T-156: ADR-0012 amendment + daily-loss accumulation tests | P2 | Formalize net daily-loss semantics. First tests ever on kill-switch input accumulation. |
| T-159: Portfolio state-machine invariant tests | P2 | Kill the stale-state bug class: every consumer of persisted portfolio fields tested for cross-day transitions. |
| T-154: Extract decisions from CHANGE_CONTROL.md → DECISION_LOG | P3 | `decisions_logged: false` in CHANGE_CONTROL.md. Governance debt, not blocking. |

---

## Phase 2 — Infrastructure Sprint (July 2026)

| Task | Priority | Notes |
|------|----------|-------|
| T-072: Model retrain + λ feature fix | P0 | ADR-0004 requires supersession for any retrain. Retrain on 2025-26 complete regular season + Finals data. Must complete by 2026-10-15. **S69 SCOPE ADDITION (authorized DECISION_LOG S69):** retrain must incorporate the three Option C feature fixes: (i) `playoff_round_multiplier` in C2 λ derivation (1.0 regular season; calibrate from NBA playoff historical data); (ii) replace regular-season opp defensive ratings with opponent's trailing-N playoff-game stats; (iii) within-series momentum feature (player scoring in current series vs rolling avg). All three derived from empirical data — no guessed multipliers. **Phase 3 START GATE:** T-072 must close (feature fixes implemented + new model passes ADR-0009 shadow gate) AND a post-fix `run_t177` backtest on available NBA data must return INCONCLUSIVE or MONOTONIC (not ANTI-PREDICTIVE, p > 0.05) before Phase 3 MLB C1 build begins. Building MLB infrastructure on a model with a known systematic λ overestimation replicates the same structural error at greater cost. |
| DS-04 injury source (T-073) | P1 | KI-011: T2 is injury-blind. Without DS-04, T2 activation generates fake alpha (injury blindness). Required before T2 active. Evaluate sources: Rotoworld, FantasyLabs, ESPN API injury reports. |
| T-077: Polymarket activation | P1 | Operator KYC. VenueAdapter already built; execution gated on KYC completion. Second venue adds line-shopping (Strategy E, +7.8% EV per EXP-014). |
| ADR-0005 draft: live capital framework | P2 | Parameters for live capital deployment: bankroll size, per-bet limits, reserve fraction, kill switch thresholds at live scale. Requires: EXP-017 positive at adequate sample, T-153 haircut complete. Cannot finalize until commercial validation is confirmed but draft can be prepared. |
| T-153 completion (spread model) | P2 | Spread model for EXIT_NET_COST_BAND (all time-remaining buckets). Unblocks ADR-0019 Tier 2 (exit mechanics fully validated). Requires G4/G5 spread data + additional regular-season spread observations. |
| ~~T-148: APR-0017 floor regression (T4 evidence standard)~~ | ~~P2~~ | ✅ DONE SESSION 72 — ADR-0028 ACCEPTED (DS sign-off Earl Ignacio 2026-06-22). G6 scoped to T1-only; T4 Tier 2 moved to T4 Activation Gate (Phase 8 pre-requisite). GG-022 RESOLVED. |

---

## Phase 3 — MLB Commercial Validation (August–September 2026)

**Phase 3 Prerequisites (GATE — do not start MLB C1 build until both are met):**
1. **T-072 CLOSED:** The three Option C λ feature fixes are implemented and the retrained model passes the ADR-0009 shadow gate (Brier improvement over v1-28483b21, ECE ≤ 0.05).
2. **Post-fix backtest passes:** `scripts/run_t177_edge_monitor.py` run on available NBA data with the fixed model returns INCONCLUSIVE or MONOTONIC — not ANTI-PREDICTIVE (p > 0.05). Rationale: if the known λ overestimation is not corrected first, EXP-017 MLB will test a structurally biased model at ADR-0024-adequate sample size. A CONFIRMED_NEGATIVE at that scale triggers ADR-0024 Tier 2 diagnostic sprint — the same root cause diagnosed in S69, found at greater cost.

This is the most strategically significant phase. Per ADR-0024, commercial validation requires a structurally adequate sample (n ≥ 500, ≥ 15 opponents, or ≥ 2 sports). MLB provides the scale and diversity that the NBA Finals window could not.

| Task | Priority | Notes |
|------|----------|-------|
| MLB C1 module | P0 | New sport integration. Data source: Baseball-Reference / Statcast API. Pull game logs, player batting/pitching stats, team context. Follows C1 module interface — no changes to C4–C8 required. |
| MLB C2 feature set | P0 | Sport-specific features: rolling batting average, slugging, OPS, pitcher strikeout rate, park factors, rest differential, home/away split. Starting pitcher overlay is the MLB equivalent of the injury T2 overlay. |
| MLB C3 model training | P0 | Train LR + Platt on MLB player props data (O/U thresholds — HR, hits, strikeouts, etc.). New model version per ADR-0004. |
| EXP-017 MLB run | P0 — commercial validation gate | Backtest MLB model edge vs actual Kalshi MLB market prices. This is the ADR-0024 commercial validation experiment. ADR-0024 Tier 1 check fires at n ≥ 150 MLB unique markets. |
| EXP-018 MLB calibration | P1 | Model vs null on MLB data. Calibration power is higher at MLB scale (hundreds of games/day). |
| ADR-0024 Tier 1 review | P0 gate | At n ≥ 150 MLB unique markets: compute EV/bet. If < -$0.03: diagnostic sprint per ADR-0024. If > 0: strong signal to proceed. If inconclusive: continue to Tier 2 floor. |
| MLB paper trading activation | P2 | Live MLB paper bets via T1 pipeline (game-day pregame only; no T4 until MLB T4 decision tree built). Venue: Kalshi (MLB markets active). Fresh $1,000 paper book (`logs/paper_portfolio_mlb.json`) — DS decision SESSION 74; separate from NBA book. |
| T-186: F-042 playoff TeamGameLog pull + v2b retrain | P1 (NBA debt, Phase 3 window) | v2-065b9510 was trained with F-042=NaN everywhere (playoff opponent defensive stats deferred). The primary Brier gain came from F-039/F-040, not the playoff compression fix. Pull playoff TeamGameLog for 8-10 NBA teams via nba_api, repopulate F-042 for training rows, retrain v2b, re-run T-177. If complete before October, deploy v2b instead of v2 in Phase 4. Can run in parallel with MLB C1/C2 build during August-September. |

---

## Phase 4 — Pre-Season Prep (October 2026)

| Task | Priority | Notes |
|------|----------|-------|
| T4 empirical gates: T-152 + T-153 | P1 | T-152 (exit events n≥50) and T-153 (spread model) complete before ADR-0019 Tier 2 closes. Needs regular-season T4 data. |
| G6 evidence review | P0 gate | Check all APR-0017 tiers against accumulated evidence: T0-A (EXP-017 CONFIRMED_POSITIVE at adequate sample?), T1 execution integrity (GG-014 confirmed?), T2 calibration trends, T3 risk controls. |
| GG-014 confirmation | P0 gate | First 2026-27 regular season paper batch (day 1): check order failure rate. T-164 fix must show ≤5% to close GG-014 G6 gate. This is the first viable production confirmation. |
| T2/DS-04 activation readiness | P2 | If DS-04 injury source is live by Phase 4, T2 can be activated for 2026-27. Requires: DS-04 built, T2 model overlay tested, T2 decision tree reviewed vs T1 non-contamination guarantee. |
| ADR-0005 finalization | P0 gate | Live capital parameters finalized once G6 evidence review confirms gate is clearable. Cannot finalize until T-153 haircut, EXP-017 commercial validation, and GG-014 confirmation all complete. |
| T-185: v2 model deploy + paper trading restart (T-185) | P0 — DS decision required | See TODO_NEXT T-185 runbook. Three prerequisite decisions: (1) NBA 26-27 book reset option A/B/C (DECISION_LOG SESSION 74); (2) deploy v2 vs v2b (T-186 completion determines this); (3) operator witnesses first paper batch. **Alpha framing: shadow gate PASSED means calibration improved (Brier/ECE); it does NOT mean alpha vs Kalshi confirmed. Deploying v2 in October is evidence-collection on an improved feature set, not a confirmed-alpha deployment. EXP-017 at adequate sample (ADR-0024) remains the alpha gate.** |
| T-116: Multi-game night stress test | P0 — before Oct 20 | PIPE-02/PIPE-03 tested only in single-game Finals context. Regular season is 10+ simultaneous games (400+ markets/night). Simulate before season start. |
| Model retrain verification | P0 | If T-186 (v2b retrain) completed during Phase 3: v2b replaces v2-065b9510 as the deploy target. Otherwise: v2-065b9510 deploys with F-042 limitation documented (ADR-0031 Known Limitations). Do not treat the v2 shadow gate PASS as validation of the playoff compression fix. |

---

## Standing Items (Monthly Cadence)

| Item | Cadence | Notes |
|------|---------|-------|
| VPS health check | Monthly | Confirm cron jobs are running, no silent failures, logs rotating correctly |
| VPS cron dark-period output review | Monthly | PIPE-02/PIPE-03/PIPE-06 crons keep firing on NBA dark-period nights. Paper trading is kill-switch halted so no bets execute, but empty runs and inference errors accumulate silently. Check VPS logs once/month: `ssh prediction-market-vps "tail -100 /opt/prediction-market-bot/logs/cron_*.log"`. Flag any non-empty error output for investigation. |
| ADR-0009 Brier tracking | Monthly (or per-game if MLB paper trading active) | Shadow model drift detection. If Brier rises > 10% over 3-week window: retrain gate triggers |
| EXP-017 running total | Per-game (MLB active) | Accumulate unique market count toward ADR-0024 Tier 1 / Tier 2 floors |
| GOVERNANCE_GAP_LOG review | Monthly | Any new OPEN entries from implementation work? |

---

## Key Dependencies and Blockers

```
GG-014 confirmation         ← 2026-27 regular season Day 1 batch (first viable test)
ADR-0005 live capital       ← EXP-017 CONFIRMED_POSITIVE + T-153 + GG-014 confirmed
T2 activation               ← DS-04 injury source (T-073) + T2 decision tree review
Exit mechanics (T-152/153)  ← Regular-season T4 trajectory + spread data
MLB paper trading           ← MLB C1 + C2 + C3 complete
EXP-017 Tier 1 check        ← n ≥ 150 MLB unique markets (August–September)
G6 clearable                ← EXP-017 CONFIRMED_POSITIVE (adequate sample) + T-153 + GG-014
```

---

## What This Plan Does NOT Cover

- **DFS pick'em (PrizePicks, Underdog, Sleeper):** Requires separate ADR before activation. Not in scope for dark period.
- **Complement arbitrage (arb/ folder):** APR-0010 not signed. Reference only — do not incorporate.
- **NFL:** Out of scope until MLB architecture is validated as the sport-extension model.
- **T4/T5 for MLB:** T4 requires live Bayesian model calibrated for baseball. Not in dark period scope. Requires separate ADR.
