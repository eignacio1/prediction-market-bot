# Session Handoff — 2026-05-31 (Structural Gap: Position Limit Stub)

**Trigger:** Operator session close — structural gap identified; handoff before new terminal
**Prior handoff:** SESSION_HANDOFF_20260530_G7READY.md

---

## ⚠️ PRIORITY #1 — BLOCKER BEFORE FINALS G2: max_concurrent_positions is a G4 stub

**This is the first thing to address in the next session. Do not proceed to any other work until this is resolved.**

### The problem

`risk.py:94` contains:
```python
"max_concurrent_positions": 10.0,  # 10 concurrent open (stub)
```

`RISK_APPETITE_CONSTRAINTS.md:42` still reads:
```
| Max open positions simultaneously | TBD at G4 — Placeholder: ≤10 concurrent markets | ...
```

**This was NEVER resolved at G4.** All other hard limits ($500/event, $1,000/day, 20% drawdown) were confirmed and documented. This one stayed as "TBD at G4" and was never sized against the actual architecture that got built in Phase 5–7.

### Why it's an active blocker right now

The check in `risk.py:418` uses `>=`:
```python
if current_open_positions >= int(_HARD_LIMITS["max_concurrent_positions"]):
    return ..., self._build_rejection(...)
```

**Current portfolio state: 9 open positions. Cap is 10. One slot remaining.**

- 6 SAS/OKC positions from Bug G legacy (pending nba_api resolution — may take another 1-2 days)
- 3 NYK/SAS Finals G1 positions (Jun 3)

**If SAS/OKC does not resolve before Finals G2 (Jun 5 or later), PIPE-03 will attempt to place 3 bets for G2 and C4 will REJECT 2 of them silently.** The system will log `concurrent_positions_limit_reached` in the audit log, but the cron output will just show fewer bets placed with no visible error.

### Why the stub is wrong for this architecture

The 10-position value was set in early Phase 3 when the system was conceived with 10 players for a single game. The actual architecture built out:

| Factor | Phase 3 assumption | Current reality |
|---|---|---|
| Players in cohort | 10 | ~80 (cohort v2) |
| Cron windows | 1 | 2 (22:00 + 01:30 UTC) |
| nba_api resolution lag | Same day | 1–3 days |
| Execution bands | T1 only | T1 active; T2/T3 skeleton |
| Games per night (regular season) | 1 (playoffs) | Up to 15 |
| Multi-band orchestrator | Not built | Built (T-084) |

In the NBA regular season, the current limit of 10 will be hit on the first multi-game night and the system will start rejecting bets — silently, correctly per its own logic, but wrong by design intent.

### What needs to happen (next session, before anything else)

1. **Derive the correct value** from the actual strategy architecture:
   - What is the max players per game × games per night × resolution lag days?
   - What does the execution bands orchestrator (T-084) imply for max simultaneous positions?
   - Does this differ between paper trading (single-game Finals) vs. regular season?
   - Consider two values: one for current paper trading phase; one for regular season G6+

2. **DS sign-off** — this is a Class B change (hard limit value change, not kill switch logic). Requires operator approval before deployment.

3. **Update three locations:**
   - `risk.py:94` — change the value and remove the "stub" comment
   - `RISK_APPETITE_CONSTRAINTS.md:42` — replace "TBD at G4 — Placeholder" with signed value + rationale
   - `DECISION_LOG.md` — log the derivation methodology and chosen value

4. **Deploy to VPS** — scp risk.py; smoke test; confirm C4 check passes with current 9-position portfolio

5. **Register as KI-016** (done — see KNOWN_ISSUES.md)
6. **Register as T-102** (done — see TODO_NEXT.md)

### Files to touch

| File | Location | Change |
|---|---|---|
| `risk.py` | `src/prediction_market_bot/c4_risk_engine/risk.py:94` | Replace stub value + comment |
| `RISK_APPETITE_CONSTRAINTS.md` | `01_SPEC/:42` | Replace TBD placeholder with signed value |
| `DECISION_LOG.md` | `03_DECISIONS/DECISION_LOG/` | Log derivation + DS sign-off |

### Broader lesson registered

This gap existed because stubs set at G4 were checked at G4 for "do they break anything?" not "are they right for the architecture we just built?" The session-start governance scan catches `decisions_logged: false` — it does NOT catch "this value was set as a placeholder and was never revisited." A second scan category needs to be added: **grep for `# stub` and `# placeholder` in source code** as part of session-start verification.

See T-103 in TODO_NEXT.md.

---

## Current System State

**Phase:** 6/7 ACTIVE (G0–G5 all closed)
**Tests:** 550/550 passing
**Capital:** NO live capital — paper trading only
**VPS:** 157.230.91.33 — cron running; all bugs fixed and deployed

**Portfolio (as of 2026-05-31T22:00 UTC):**
- Bankroll: $683.41 | Realized PnL: $0.00 | Realized drawdown: 0.00%
- 9 open positions: Fox YES ×3 + SGA NO ×3 (SAS/OKC G7, pending nba_api) + KAT YES + OG NO + Brunson NO (NYK/SAS Finals G1, Jun 3)
- **Kill switch COLD — will not fire**
- G6 progress: 0/30 resolved bets

**PIPE-03 operational:**
- BAND_REGISTRY: OK, no violations
- Idempotency: working correctly (confirmed May 31 01:30 cron)
- PIPE-03R: running at 06:00 UTC daily; SAS/OKC resolution pending nba_api lag

---

## Cron Schedule (VPS, no changes needed)

```
21:30 UTC  — PIPE-02 inference
22:00 UTC  — PIPE-03 early bets
01:30 UTC  — PIPE-03 late bets
06:00 UTC  — PIPE-03R resolve-only
```

---

## Next Session Priority Queue

| Priority | Task | Notes |
|---|---|---|
| **1 — BLOCKER** | **T-102: Fix max_concurrent_positions stub** | Risk of Finals G2 bet rejection active right now; requires architectural analysis + DS sign-off + VPS deploy |
| 2 | **T-103: Add stub scan to session-start protocol** | `grep -rn "# stub\|# placeholder" src/` — add to MEMORY_BANK.md governance scan section |
| 3 | Check SAS/OKC resolved | `ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 "cat /opt/prediction-market-bot/logs/paper_portfolio.json"` |
| 4 | T-070 — accumulate 30 resolved paper bets | Count goes up once SAS/OKC resolves |
| 5 | T-077 — Polymarket KYC (operator) | polymarket.com → KYC → API key → .env → RUNBOOK |
| 6 | T-091 — C7 paper P&L monitoring alert | WARNING at -$50; L2 at -$100; needs DS threshold sign-off |

---

## Strategic Decisions This Session

| Decision | Canonical Reference |
|---|---|
| max_concurrent_positions: 10 is a stub that was never resolved at G4 — identified as structural gap | Operator message 2026-05-31; KI-016 registered; T-102 registered |
| Session-start scan must include grep for `# stub` / `# placeholder` in src/ | T-103 registered |

---

## Governance State

- 7 documents with `decisions_logged: false` (T-093–T-099): all LOW priority, non-blocking
- KI-014 and KI-015: updated to RESOLVED in KNOWN_ISSUES.md this session
- KI-016 (new): max_concurrent_positions stub — HIGH, active blocker
- Governance scan last run: clean (no new debt beyond T-093–T-099)

---

## Files Changed This Session

| File | Change |
|---|---|
| `10_INFRA_OPERATIONS/KNOWN_ISSUES.md` | KI-014 and KI-015 marked RESOLVED; KI-016 added |
| `04_EXECUTION/TODO_NEXT.md` | T-102 and T-103 added as top priorities |
| `11_MEMORY_HANDOFF/MEMORY_BANK.md` | Updated current state snapshot |
| `11_MEMORY_HANDOFF/SESSION_HANDOFF_20260531_STUBGAP.md` | This file |
