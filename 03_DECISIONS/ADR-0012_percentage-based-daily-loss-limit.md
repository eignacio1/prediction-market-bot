# ADR-0012 — Replace Zombie Daily Loss Limit with Percentage-Based Threshold

**Status:** ACCEPTED — 2026-06-02  
**Decision makers:** DS (Earl Ignacio)  
**Supersedes:** `max_daily_loss_usd: 1000.0` in `_HARD_LIMITS` (retroactive DECISION_LOG.md entry 2026-05-29, confirmed G4/ADR-0004)  
**Superseded by:** —  
**Related:** KI-018 (zombie daily loss limit), ADR-0004 (G4 risk framework acceptance), ADR-0010 (band Kelly hierarchy + reserve mandate)

---

## Context

### The defect (KI-018)

`_HARD_LIMITS["max_daily_loss_usd"] = 1000.0` was calibrated against an assumed $1,000 bankroll at G4. At a $1,000 starting bankroll, the operative kill switches are:

| Trigger | Threshold | Fires at loss |
|---------|-----------|----------------|
| `max_drawdown_pct = 0.20` | 20% realized drawdown | $200 |
| `max_daily_loss_usd = 1000.0` | $1,000 daily loss | $1,000 |

The drawdown kill switch fires first — at $200 loss. The daily loss limit requires losing the **entire bankroll** before it activates. It is structurally inactive at any bankroll ≤ $1,000.

The system has one operative kill switch, not two. The second check exists in code but provides no additional protection.

### Why two independent kill switches matter

Two kill switches guard against different failure modes:
- **Drawdown (20%):** Guards cumulative losses across multiple sessions. Fires when the portfolio has declined meaningfully from its historical peak.
- **Daily loss (%):** Guards single-session catastrophic loss — a burst of bad bets in one cron window. Should fire independently of where the drawdown stands.

With `max_daily_loss_usd = $1,000` at a $1,000 bankroll, a session could drain 19% of capital ($190) in a single run and neither kill switch fires. The drawdown check fires at 20% cumulative, not per-session. The daily loss check is inaccessible. This gap is KI-018.

---

## Decision

Replace `max_daily_loss_usd: 1000.0` in `_HARD_LIMITS` with a percentage-based constant:

```python
MAX_DAILY_LOSS_PCT: float = 0.15
```

The daily loss threshold is computed from the `initial_bankroll` passed to `RiskEngine`:

```python
self._daily_loss_threshold = self._initial_bankroll * MAX_DAILY_LOSS_PCT
```

At $1,000 starting bankroll: threshold = **$150** (15%). This fires before the 20% drawdown kill switch ($200), restoring independent layering.

### Threshold derivation: why 15%?

| Candidate | $1,000 threshold | Relationship to drawdown (20% = $200) |
|-----------|-----------------|----------------------------------------|
| 5% | $50 | Too tight — 3–4 normal losing bets fire it |
| 10% | $100 | Conservative; allows ~2 max-size paper bets |
| **15%** | **$150** | Allows ~3 max-size bets; fires before 20% drawdown |
| 20% | $200 | Simultaneous with drawdown — no independent layering |
| 25% | $250 | Fires after drawdown — same defect as original |

15% is the highest round percentage that fires strictly before the 20% drawdown kill switch. At current paper scale (~$10–80/bet from Kelly sizing), 15% = $150 allows ~2–15 bets in a single session before triggering — sufficient runway for a full paper run while preventing catastrophic single-session loss.

### `initial_bankroll` parameter

`RiskEngine.__init__()` gains an optional `initial_bankroll: float | None = None` parameter. If omitted, it defaults to `bankroll` (backward-compatible). Callers that construct a RiskEngine mid-session should pass the session-start bankroll as `initial_bankroll` to hold the threshold stable across a run.

This is required because `bankroll` decreases after each bet in the paper system — using the current bankroll would cause the threshold to shrink mid-session, creating a feedback loop where a losing session becomes progressively harder to continue.

---

## Consequences

**Positive:**
- Daily loss kill switch is operationally active at paper bankroll scale for the first time.
- Two independent kill switches, as intended.
- `initial_bankroll` parameter enables correct threshold stability across multi-bet sessions.
- Percentage-based threshold scales automatically with bankroll changes between sessions.

**Negative / risks:**
- Callers that construct `RiskEngine` without `initial_bankroll` (existing scripts that have not been updated) use `bankroll` as the initial reference — correct behavior for single-bet calls but slightly less conservative for multi-bet sessions if the engine is not refreshed.
- The 15% threshold is calibrated to the current paper scale. Requires formal review at G6 when live bankroll is established. Register in ADR obligations for G6 risk review.

**Verification gate:** `test_daily_loss_pct_at_threshold_triggers_kill_switch` and `test_daily_loss_pct_below_threshold_passes` added to `test_c4_risk.py`.

---

## G6 obligation

The `MAX_DAILY_LOSS_PCT = 0.15` threshold must be reconsidered at G6 when the live bankroll is set. A higher-bankroll deployment may warrant a tighter percentage (e.g., 10% at $10k bankroll = $1,000, matching the original nominal limit). Register in DECISION_LOG.md G6 checklist.
