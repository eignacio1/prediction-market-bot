# Risk Appetite and Constraints — Prediction Market Trading Bot

**Purpose:** Define all hard limits, prohibited behaviors, and risk boundaries. These are enforced programmatically in Phase 6+ and govern research-phase decisions immediately.  
**Owner (role):** Risk/Control Owner (RCO)  
**Last reviewed:** 2026-07-02 (documentation-remediation pass — the Hard Limits table below still read "TBD at G4 — Placeholder" for all three primary limits despite this same document's own footer, dated 2026-06-02, stating the real confirmed values. Table body and footer had drifted apart; this pass reconciles them against the live-enforced values in `risk.py`.)  
**Next review:** Quarterly at minimum, or on any `_HARD_LIMITS` change in `risk.py` (should be logged here same-session per Hard Rule 7, not left to the quarterly cadence)  
**Staleness triggers:** Capital amount changes; venue confirmed (venue rules may impose stricter limits); strategy class changes; live capital authorization (G6)  
**Upstream links:** PROJECT_CHARTER.md, VISION_OUTCOMES.md  
**Downstream links:** REQUIREMENTS.md (FR-05, FR-09), 02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md, 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0006 (exposure-based risk framework), ADR-0012 (percentage-based daily loss), ADR-0026 (portfolio free-cash invariant)  
**Confidence:** 8/10 — Structure is authoritative; primary numerical thresholds are now live-enforced (not placeholders) and cross-checked directly against `risk.py` source as of this review. GG-071 (below) is an open question about whether these limits are *sufficient*, not about their current value.
**Decisions logged:** true — T-097 logged 2026-06-02: $500/bet cap + 20% drawdown confirmed via G4/ADR-0004 (retroactive 2026-05-29 entry); $1,000/day limit superseded by ADR-0012 (MAX_DAILY_LOSS_PCT=0.15). See DECISION_LOG.md 2026-06-02 and 2026-07-02 (table-body reconciliation).

**⚠️ Open question carried from GG-071 (registered SESSION 113, 2026-07-02):** a forward-time compounding Monte Carlo found that even a real, positive-edge band (T1 MLB, 53.06% observed win rate) produces a 46.45% one-year probability of permanently tripping the 20% max-drawdown kill switch under proportional-stake compounding at real bet cadence. The limits below are correctly enforced as written — the open question is whether "20% max drawdown, enforced" is itself a sufficient risk-appetite statement once cadence is accounted for. T-223 (unassigned priority) is the follow-up review. Do not treat this document as settling that question just because the dollar/percentage values below are current.

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

## Hard Limits (Live Capital Phase — Phase 8+; also enforced identically in Phase 6/7 paper trading)

*These were placeholders pending G4 evidence; they are now the live-enforced values in `src/prediction_market_bot/c4_risk_engine/risk.py` (`_HARD_LIMITS` dict + module constants), confirmed by direct source read 2026-07-02. Still subject to formal re-derivation via ADR at G6 per the standing 2026-05-29 obligation — "confirmed and enforced today" is not the same claim as "formally re-derived for live bankroll," and that gap remains open.*

| Limit | Threshold (current, enforced) | Trigger Action | Enforcement Method | Source |
|-------|-----------|---------------|-------------------|--------|
| Max single-event position | `max_single_event_exposure_usd = $500.00` (flat cap, not a % of capital as originally placeholder-scoped — caps Kelly output regardless of bankroll size) | Immediate order size clamp to $500 | Pre-order risk check | `risk.py` `_HARD_LIMITS`, ADR-0006 |
| Max daily loss | `MAX_DAILY_LOSS_PCT = 0.15` (15% of session-start bankroll) | Kill switch auto-trigger (daily circuit breaker, resets next session) | Real-time PnL monitor | `risk.py`, ADR-0012 (superseded the original `max_daily_loss_usd` placeholder) |
| Max portfolio deployment | `max_portfolio_deployment_pct` (aggregate open stake ≤ 60% of equity) | New order REJECTED if it would breach | Pre-order aggregate exposure check | `risk.py`, ADR-0026 |
| Max order rate | Still TBD (venue-dependent) — **unchanged, genuinely open, not resolved by this remediation pass** | Order rejection + alert | Rate limiter at execution layer | Not yet implemented as a hard limit |
| Max drawdown (realized, permanent) | `max_drawdown_pct = 0.20` (20% of capital) — **permanent kill switch, not the 7-day rolling window this row originally specified; the implemented mechanic is simpler (all-time realized drawdown) than what was placeholder-scoped** | Kill switch trips, bot halted, requires manual review to resume | PnL monitor + alert | `risk.py` `_HARD_LIMITS`, ADR-0006 |
| Kill switch response time | ≤60 seconds | N/A (is the limit itself) | Tested at G5 (0.340ms actual, KS-C8D7D90AF942) — well within tolerance | NFR-03 |

**⚠️ GG-071 caveat (see header):** these limits are correctly enforced as written, but a positive-EV band can still compound its way into tripping the 20% permanent kill switch at real bet cadence (46.45% 1yr probability observed for T1 MLB). The table above answers "what is the limit," not "is the limit calibrated to cadence" — that is still open.

*Fractional Kelly fraction (see Position Sizing Framework below): `DEFAULT_KELLY_FRACTION = 0.25` — this row's original "starting assumption: 0.25" was never revised and turned out to match the value that shipped; not re-derived from new evidence, just confirmed unchanged.*

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
- **Fractional Kelly:** Bet size = f* × fraction (`DEFAULT_KELLY_FRACTION = 0.25` — confirmed unchanged from the original starting assumption; live in `risk.py`)
- **Rationale:** Full Kelly maximizes long-run growth but produces extreme drawdowns and requires perfectly calibrated probabilities. Fractional Kelly is more robust to miscalibration.
- **Constraint:** Kelly output is always subject to max single-event position hard limit above.

*Position sizing formula must be validated in backtesting before live use. Methodology documented in 08_MODEL_RISK_GOVERNANCE/METHODOLOGY.md.*
