# ADR-0006 — Risk Framework: Delete Count Gate; Pipeline + Kelly + Kill Switch Are the Risk Controls

**Purpose:** Formally remove the count-based position limit from C4 and establish that the filtering pipeline, Kelly criterion, and drawdown kill switch constitute the complete risk framework for this architecture.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-06-01 (accepted at T-102 resolution)  
**Next review:** G6 Live Capital Gate — revisit all `_HARD_LIMITS` values when real bankroll is set  
**Staleness triggers:** Execution architecture changes (new bands active, new venues, real-time data); bankroll changes at G6  
**Upstream links:** ADR-0002 (forecast-only), ADR-0004 (model class), RISK_APPETITE_CONSTRAINTS.md  
**Downstream links:** `c4_risk_engine/risk.py`, `run_paper_trade.py`, EXECUTION_ARCHITECTURE.md  
**Decision references:** ADR-0001 (Compass OS), GG-001 (GOVERNANCE_GAP_LOG.md)  
**Confidence:** 10/10 — DS sign-off granted 2026-06-01; code change applied same session

---

## Status

`ACCEPTED` — DS sign-off 2026-06-01 (T-102)

---

## Context

`_HARD_LIMITS["max_concurrent_positions"] = 10.0` was set at G4 as a stub for a system conceived with 10 players for a single game. It was never resolved at G4. The actual architecture built in Phases 5–7:

| Assumption at G4 | Reality at G7 |
|---|---|
| ~10 players | ~80-player cohort |
| T1 only | T1–T5 bands built; T1 ACTIVE, T2/T3 SKELETON |
| 1 cron window | 2 cron windows (22:00 + 01:30 UTC) |
| 1 game per session | Up to 15 games/night (regular season) |
| nba_api resolves same day | 1–3 day resolution lag |
| No multi-band orchestrator | T-084 built; CONFIRM/FADE/NEUTRAL rules |

The count gate was architecturally incoherent with the system it was meant to protect. Count is the wrong primitive for a multi-band quant execution system. In utopia — the system working as designed — thousands of trades per game flow through the pipeline across time horizons. A hard limit of 10 simultaneous positions would fire on the first active regular season night and silently reject valid bets.

More critically: a count gate does not control risk. It controls *number*. Two things are not the same. Ten small bets on highly correlated players in one game carry more correlated risk than 500 well-Kelly-sized bets across 15 independent games.

---

## Decision

**Delete `max_concurrent_positions` from `_HARD_LIMITS`. Remove CHECK 3 from `risk.py`. Remove `current_open_positions` parameter from the `evaluate_forecast()` interface. No replacement count gate.**

The complete risk framework is:

| Control | Location | What it governs |
|---|---|---|
| Edge threshold (`MIN_EDGE_TO_APPROVE = 0.02`) | C4 CHECK 4 | No positive EV → no bet |
| Kelly criterion (`DEFAULT_KELLY_FRACTION = 0.25`) | C4 `_compute_kelly_size()` | Edge × confidence → position size |
| Kelly fraction by band (T1=0.25, T2=0.20, T3=0.10…) | ExecutionBands | Lower confidence bands → smaller sizes |
| Single-event exposure cap (`max_single_event_exposure_usd = $500`) | C4 CHECK 6 | Any one bet capped at $500 |
| Minimum bet floor (`MIN_BET_USD = $10`) | C4 CHECK 7 | Trivially small bets rejected |
| Daily loss limit (`max_daily_loss_usd = $1,000`) | C4 CHECK 1 → KILL_SWITCH | Bad day brake |
| Drawdown kill switch (`max_drawdown_pct = 0.20`) | C4 CHECK 2 → KILL_SWITCH | Portfolio-level emergency stop |

The filtering pipeline is the primary selection mechanism. C4 is a safety net, not a filter. The kill switch is the structural backstop. If the model is systematically wrong, it bleeds to 20% drawdown and stops. There is no scenario in which a count of open positions is the correct variable to monitor.

---

## Consequences

**Positive:**
- Unlocks the actual design intent: every market evaluated on its merits through the pipeline
- Regular season operation with 15 games/night will not artificially stall
- Multi-band orchestrator can fire on all time horizons without an arbitrary ceiling
- The `evaluate_forecast()` interface is simpler (one fewer parameter)

**Risks and mitigations:**
- **Kelly miscalibration risk**: If the model dramatically overestimates edge on many markets simultaneously, total outstanding exposure could be large. Mitigation: $500/event cap limits maximum loss per market; 20% drawdown kill switch stops the run before catastrophic loss.
- **Correlation risk (game-night blowout)**: All player props in one game are correlated — a blowout night hurts all simultaneously. Mitigation: Kelly fraction reduction by band already accounts for signal uncertainty. This is a known risk registered in RISK_APPETITE_CONSTRAINTS.md as a soft limit (single-market concentration advisory).
- **Resolution lag**: Positions accumulate during nba_api lag (1–3 days). Without a count gate, total outstanding can grow. Mitigation: PaperTrader tracks and deducts stakes from bankroll; the bankroll floor (drawdown kill switch) is the binding constraint.

**Note on future G6 revisit:** All `_HARD_LIMITS` values were set for a $1,000 paper bankroll. At live capital (ADR-0005), these must be re-derived and confirmed via new APR before any real-money execution. This ADR does not make that decision — it only removes the count gate.

---

## Alternatives Considered

**Alternative 1: Increase the count limit (e.g., 10 → 500)**  
Rejected. Changing a wrong primitive to a higher wrong number does not fix the architecture. The primitive itself (count) is wrong.

**Alternative 2: Replace with per-player exposure cap + total portfolio exposure cap**  
Rejected. These are still aggregate limits that will fire on active game nights and block the pipeline's intent. Kelly + drawdown already handle these risk dimensions correctly.

**Alternative 3: Keep count gate as a circuit breaker at a very high limit (e.g., 10,000)**  
Rejected. A limit set so high that it never fires has zero risk management value and creates false precision in documentation.

---

## Implementation

| File | Change |
|---|---|
| `c4_risk_engine/risk.py:94` | Remove `"max_concurrent_positions": 10.0` from `_HARD_LIMITS` |
| `c4_risk_engine/risk.py:36` | Remove `MAX_CONCURRENT_POSITIONS` from docstring |
| `c4_risk_engine/risk.py:284` | Remove `current_open_positions: int = 0` parameter |
| `c4_risk_engine/risk.py:417–437` | Remove CHECK 3 entirely |
| `run_paper_trade.py:213,305,341` | Remove `n_open_pos` tracking and parameter pass |
| `tests/test_c4_risk.py` | Remove 2 concurrent-position tests; update coverage comment |
| `01_SPEC/RISK_APPETITE_CONSTRAINTS.md:42` | Remove "Max open positions simultaneously" row |
| `02_ARCHITECTURE_DESIGN/EXECUTION_ARCHITECTURE.md` | Remove "Check: concurrent positions ≤ limit" from decision cycle |

**DS sign-off:** Earl Ignacio, 2026-06-01  
**APR reference:** Covered under T-102 resolution; Class B change (hard limit modification)
