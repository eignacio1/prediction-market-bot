# Risk Appetite and Constraints — Prediction Market Trading Bot

**Purpose:** Define all hard limits, prohibited behaviors, and risk boundaries. These are enforced programmatically in Phase 6+ and govern research-phase decisions immediately.  
**Owner (role):** Risk/Control Owner (RCO)  
**Last reviewed:** 2026-05-21  
**Next review:** G1 Spec Gate; then quarterly at minimum  
**Staleness triggers:** Capital amount changes; venue confirmed (venue rules may impose stricter limits); strategy class changes; live capital authorization (G6)  
**Upstream links:** PROJECT_CHARTER.md, VISION_OUTCOMES.md  
**Downstream links:** REQUIREMENTS.md (FR-05, FR-09), 02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md, 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — Structure is authoritative; specific numerical thresholds require venue confirmation and G4 backtesting evidence to finalize  

---

## RULE 0 — Governing Principle

**No limit in this document is discretionary. All limits must be enforced programmatically in Phase 6 (paper trading) and Phase 8 (live capital). Human override of a hard limit requires a formal ADR with RCO + PO approval.**

---

## Phase-by-Phase Capital Authorization

| Phase | Capital Status | What's Permitted |
|-------|--------------|-----------------|
| 0–4 (Research) | $0 authorized | Backtesting, signal research, simulation on historical data |
| 5 (Ops Readiness) | $0 authorized | Kill switch testing, observability wiring, rollback drills |
| 6 (Paper Trading) | Simulated only | Live data consumption; hypothetical orders; no real capital |
| 7 (Promotion Gate) | $0 until G6 cleared | Gate review, compliance instantiation, approval documentation |
| 8+ (Live Capital) | Per limits below, after G6 sign-off | Real order placement within hard limits |

---

## Hard Limits (Live Capital Phase — Phase 8+)

*These are targets; final thresholds are confirmed at G4 (based on backtest evidence) and frozen at G6.*

| Limit | Threshold | Trigger Action | Enforcement Method |
|-------|-----------|---------------|-------------------|
| Max single-event position | TBD at G4 — Placeholder: ≤5% of total capital | Immediate order rejection | Pre-order risk check |
| Max daily loss | TBD at G4 — Placeholder: ≤10% of total capital | Kill switch auto-trigger | Real-time PnL monitor |
| Max open positions simultaneously | TBD at G4 — Placeholder: ≤10 concurrent markets | Order rejection | Position inventory check |
| Max order rate | TBD at G6 (venue-dependent) | Order rejection + alert | Rate limiter at execution layer |
| Max drawdown (rolling 7-day) | TBD at G4 — Placeholder: ≤20% of capital | Human review required; bot paused | PnL monitor + alert |
| Kill switch response time | ≤60 seconds | N/A (is the limit itself) | Tested at G5; documented in runbook |

*Placeholder thresholds are conservative starting points. They require G4 backtesting evidence and a formal CHANGELOG entry when updated.*

---

## Prohibited Behaviors (All Phases)

| Prohibited Behavior | Reason | Enforcement |
|--------------------|--------|-------------|
| Look-ahead bias in any experiment | Silent contaminator that makes backtests meaningless | Data snapshot discipline; enforced in experiment records |
| Storing API credentials in plaintext or code | Security invariant | SECRETS_HANDLING.md; enforced at code review |
| Shadow docs (decisions made outside directory) | Root cause of previous iteration's context rot | Anti-shadow-doc rule: 72h absorption rule |
| Incorporating arb/ folder without ADR | Risk of data/process contamination recurrence | SCOPE_IN_OUT.md; enforced at DIR |
| Deploying real capital without G6 sign-off | Unacceptable risk before evidence thresholds met | APPROVALS_REGISTER.md; no credentials before ACC-0002 approved |
| Manual override of programmatic risk limits without ADR | Defeats purpose of hard limits | RCO approval required for any override |
| Running live models on training data (data leakage) | Inflates apparent performance | Train/test split enforcement in all experiment records |
| Spoofing-like patterns (place-and-cancel at scale) | Likely prohibited by venues and potentially illegal | Order logic constraint; rate limiter |
| Using unvalidated signals in live capital phase | Insufficient evidence base for real money | Signals must pass G4 evidence gate before live use |

---

## Soft Limits (Advisory — Trigger Review, Not Auto-Halt)

| Limit | Threshold | Trigger Action |
|-------|-----------|---------------|
| Single-market concentration | >10% of daily volume in one market | Alert + human review |
| Forecast confidence | <55% probability assigned to top outcome | Reduce position size to minimum (do not skip) |
| Live performance vs backtest deviation | Brier score degrades >0.05 vs backtest baseline | MO/V review; possible model re-validation |
| Directory freshness (M1 metric) | <85% of artifacts reviewed within SLA | DIR agenda item; escalate at <75% |

---

## Position Sizing Framework (Research Phase — Design)

The bot will use **fractional Kelly** sizing (not full Kelly) to limit volatility:

- **Kelly formula:** f* = (bp - q) / b, where b = odds received, p = P(win), q = 1-p
- **Fractional Kelly:** Bet size = f* × fraction (fraction TBD at G4; starting assumption: 0.25)
- **Rationale:** Full Kelly maximizes long-run growth but produces extreme drawdowns and requires perfectly calibrated probabilities. Fractional Kelly is more robust to miscalibration.
- **Constraint:** Kelly output is always subject to max single-event position hard limit above.

*Position sizing formula must be validated in backtesting before live use. Methodology documented in 08_MODEL_RISK_GOVERNANCE/METHODOLOGY.md.*
