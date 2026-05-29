# Context Pack — CP-2026-05-29_phase6-active

**Created:** 2026-05-29  
**Purpose:** Phase 6/7 state snapshot. Full operational picture after G5 closure, VPS deployment, Phase 7 infrastructure build, and handoff audit repair. Read alongside MEMORY_BANK.md when deeper context is needed.  
**Replaces:** CP-2026-05-28_G5-readiness.md (superseded)  
**Frozen:** Yes — point-in-time snapshot. Do not update; create a new CP instead.

---

## One-Paragraph State

G0–G5 are all closed. Phase 6 (paper trading) is live. Phase 7 infrastructure is fully built but not yet activated for live capital. The VPS (157.230.91.33, DigitalOcean NYC3) runs a dual-window cron: PIPE-02 inference at 21:30 UTC, PIPE-03 paper trading at 22:00 UTC (early, 7pm ET games) and 01:30 UTC (late, 9pm+ ET games), PIPE-03R resolution-only at 06:00 UTC. The production model is v1-28483b21 (LR+Platt, 78 features, FEATURE_VERSION 1.2.0, Brier +0.0039 vs null, EV +$0.0958/bet). All 16 experiments (EXP-001–016) are complete; all 9 hypotheses are resolved. G6 gate requires 30 resolved paper bets with positive P&L (APR-0016, revised from 50 per seasonal constraint). NBA Finals end ~2026-06-22; NBA dark period follows until ~2026-10. 533/533 tests passing.

---

## Gate and Phase Status

| Gate | Status | Date | Key Approval |
|------|--------|------|-------------|
| G0–G5 | ✅ ALL CLOSED | 2026-05-22 to 2026-05-28 | APR-0002 through APR-0013 |
| G6 Live Capital | 🟡 IN PROGRESS | — | 30 paper bets + positive P&L (APR-0016) |
| Phase 6 Paper Trading | 🟢 ACTIVE | 2026-05-29 | APR-0007 |
| Phase 7 Infrastructure | ✅ BUILT | 2026-05-29 | Not yet activated (awaits G6) |

---

## Strategic Decisions (This Sprint — 2026-05-29)

| Decision | Canonical Reference |
|----------|-------------------|
| G6 threshold 50 → 30 resolved paper bets | APR-0016 (APPROVALS_REGISTER.md) |
| NBA dark period (~2026-06-22 to ~2026-10) = build window, not idle | DECISION_LOG.md (2026-05-29) |
| Handoff procedures upgraded — strategic decisions must be captured mid-session | LL-008, MEMORY_BANK Invariant #9, /session-end Step 1A |
| Pilot experiment before infrastructure (LL-009) | LESSONS_LEARNED.md LL-009 |
| EXP-016 HYP-009 CONFIRMED — playoff paper bets = full G6 evidence | HYPOTHESES.md, KI-008 RESOLVED |

---

## Production System

```
Model:    v1-28483b21 | LR+Platt | 78 features | FEATURE_VERSION 1.2.0
          Brier +0.0039 vs null | ECE 0.0342 | EV +$0.0958/bet
VPS:      157.230.91.33 | DigitalOcean NYC3 | Ubuntu 24.04 | Python 3.12 | sklearn 1.8.0
SSH:      ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33
GitHub:   github.com/eignacio1/prediction-market-bot (private)
Tests:    533/533 passing
```

**Active cron:**
```
21:00 UTC — Health check
21:30 UTC — PIPE-02 inference (run_pregame.py)
22:00 UTC — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

---

## All Experiment Results

| Exp | Verdict | Key Metric |
|-----|---------|-----------|
| EXP-001–003 | ✅ G4 evidence | Brier +0.0026 to +0.0056; ECE < 0.05 |
| EXP-004 | HYP-003 ✅ CONFIRMED | EV +$0.0855/bet vs Kalshi vig |
| EXP-005 | ✅ Model refresh | 5-season data; prod candidate |
| EXP-006–009 | Qual signals explored | EXP-007 +0.0017 Brier signal; L3 needs non-linear |
| EXP-010 | ✅ EV re-est | EV +$0.0958/bet with refreshed model |
| EXP-011 | LR RETAINED | HGBC Δ=-0.0008; below ADR-0004 threshold |
| EXP-012 | HYP-006 🔴 FALSIFIED | opp_def_rating Δ Brier = 0.0000; FEATURE_VERSION stays 1.2.0 |
| EXP-013 | HYP-007 🔴 FALSIFIED | NB Brier 0.2671 vs LR 0.2461 |
| EXP-014 | ✅ Line shopping | +7.8% max EV; ~51–104 locks/season |
| EXP-015 | HYP-008 🔴 FALSIFIED | T3 EV ratio 0.84; T3 = FADE gate only |
| EXP-016 | HYP-009 ✅ CONFIRMED | Δ Brier = -0.0010; playoff bets = full G6 evidence |

---

## Phase 7 Infrastructure (Built, Not Yet Activated)

| Component | File | Status |
|-----------|------|--------|
| VenueRouter | c5_execution/venue_router.py | ✅ Built; kalshi_only now; best_price when Polymarket live |
| Market mapper | c5_execution/market_mapper.py | ✅ Built; accent/apostrophe normalization |
| Complement lock scanner | c5_execution/complement_lock_scanner.py | ✅ Built; detection-only (APR-0010 gates execution) |
| MultiBandOrchestrator | execution_bands_orchestrator.py | ✅ Built; T3>T2>T1 priority rules |
| ScoringDistributionModel | c3_forecasting/scoring_distribution.py | ✅ Built; NB multi-line pricing |
| TeamStatsStore | c1_signal_ingestion/team_stats_store.py | ✅ Built; dormant (EXP-012 falsified primary use) |
| PIPE-05 T2 skeleton | run_t2_sameday.py | ✅ Built; activate when DS-04 registered |
| PIPE-06 T3 skeleton | run_t3_pretip.py | ✅ Built; activate when Polymarket live |

---

## Next Actions (Priority Order)

| Task | Priority | Type | Notes |
|------|----------|------|-------|
| T-070: 30 paper bets | HIGH | Passive/cron | 0/30; dual-window active |
| T-077: Polymarket KYC | HIGH | Operator action | polymarket.com → KYC → API key |
| T-073: DS-04 qual source | MED | DS decision | First new qual source beyond PAM |
| T-081: APR-0010 DS sign-off | MED | Operator action | Activates complement lock execution |
| Dark period build queue | — | Active when dark | T-077, T-073, ADR-0005 draft, Phase 8 prep |

---

## Known Issues (Open)

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| KI-010 | Inter-series gap before Finals (3–7 day zero-bet window) | MED | OPEN |
| KI-011 | Key player injury eliminates market category mid-paper run | MED | OPEN |
| KI-012 | Negative paper P&L disqualifies G6 at any bet count — no monitoring threshold | MED | OPEN |
| KI-013 | Model staleness: v1-28483b21 trained through 2026; 5+ months stale when 2026-27 opens | MED | OPEN |
| OQ-021 | L3 amplification needs non-linear model or more data | — | Non-blocking |
| OQ-022 | nba_api backup source — register before G6 | — | Non-blocking |

---

## Anti-Erosion Invariants (9 total — see MEMORY_BANK.md for full list)

Critical ones:
- arb/ = REFERENCE ONLY (APR-0010 required)
- No real capital until G6 (ADR-0005)
- **G6 gate = 30 resolved paper bets** (APR-0016 — NOT 50)
- Strategic decisions → DECISION_LOG immediately, not at session end
- 80% context window → trigger /session-end immediately

---

## "Do Not Break" Rules

1. No conditional language ("may," "could," "possibly") in canonical registers — governance failure (LL-008)
2. Pilot experiment before infrastructure build (LL-009)
3. FEATURE_VERSION = 1.2.0 (NOT 1.3.0 — falsified by EXP-012)
4. BOT_C4_ACTIVE must NOT be set in ENV-01 or ENV-02
5. Work wifi blocks Kalshi API — use any other network
