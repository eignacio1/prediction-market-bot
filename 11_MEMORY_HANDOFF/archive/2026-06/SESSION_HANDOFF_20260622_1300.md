# Session Handoff — 2026-06-22T13:00Z (SESSION 66)

**Trigger:** Session end — design task complete; context near limit  
**Last commit:** `97e66ae` (main) — no new code commit this session (design-only artifacts)

---

## Status

- **Phase:** 6/7 ACTIVE (dark period — NBA Finals over, MLB season ongoing)
- **Tests:** 988/988 passing (no code changes this session)
- **Capital:** NO live capital — paper trading only; book halted at drawdown kill switch (25.12%)
- **VPS:** 157.230.91.33 — cron dormant (dark period); HEAD `97e66ae` unchanged
- **Paper bets:** 158/30 resolved (G6 gate passed on count; FAILING on P&L — kill switch halted book)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T4 immediate execution principle — no time mandates; staleness check is the only execution gate | DS directive: "the second the filtering mechanism has appropriately routed and filtered which bet/trade/contract to be placed where — it NEEDS to execute right then and there. Nothing can be held." Holding for an execution window destroys edge by the time the window opens. | ADR-0029 §Design Principles Principle 1 | DS |
| T4 = 11 sub-bands organized by information class, not time buckets | Time buckets are "arbitrary band segments" — CAN serve as reference points but cannot be the taxonomy definition. The filtering mechanism, decision tree, model class, and edge window duration are the correct organizing principle. Sub-bands: T4-MICRO, T4-STAGED, T4-EVENT, T4-LINEUP, T4-FLOW, T4-SENTIMENT, T4-PROJ, T4-ARITH, T4-BOUNDARY, T4-CORR, T4-EXIT. | ADR-0029 §Sub-Band Taxonomy | DS |
| T4-PROJ dynamic Kelly schedule supersedes ADR-0010 monolithic T4=0.20 | ADR-0010 anchor (0.20 at σ_λ=0.50, Q4 reference) was correct but the schedule must extend to all game phases. EARLY floor=0.010; MID formula-derived; LATE 0.078–0.167; NEAR-CERTAIN capped at 0.25. The 0.20 was the Q4 anchor point, not the universal T4 Kelly. | ADR-0029 §T4-PROJ Kelly Schedule; supersedes ADR-0010 for T4 | DS |
| FLOW-BLOWOUT is the primary carrier of blowout-context consequences | DS confirmed: bet on CONSEQUENCES of blowout state on individual player markets (trailing star lambda ↑; leading star lambda ↓; leading backup lambda ↑) — NOT on game outcome. Bidirectional edge: both expansion and contraction produce signal. | ADR-0029 §T4-FLOW FLOW-BLOWOUT tree | DS |
| T4-CORR: convergence is not correlation — N independent signals in same direction = stronger evidence | Convergence across mechanistically independent trees (T4-EVENT + T4-FLOW + T4-PROJ all pointing YES) is confirmed evidence, not a correlation discount. T4-CORR applies convergence_factor (EXP-derived). Correlation discount only applies when signals share a common cause. | ADR-0029 §T4-CORR | DS |
| ADR-0028 T4 Activation Gate PLACEHOLDER completed by ADR-0029 | T-179 was registered specifically because the ADR-0028 T4 Activation Gate section was DESIGN INCOMPLETE pending T-179. ADR-0029 is the T-179 output and formally replaces that placeholder with per-sub-band gate criteria. | ADR-0028 §T4 Activation Gate; ADR-0029 §T4 Activation Gate section | DS |
| GG-038: T4 kill switch SLA must be ≤5s (new governance gap) | Current NFR-03 = 60s. At 60 calls/min, 60s = 60 additional bets after kill trigger. Continuous T4 evaluation makes this unacceptable. New ADR required amending NFR-03 for T4 before Phase 8. | GOVERNANCE_GAP_LOG GG-038 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-179 — ADR-0029 DRAFTED** | 🔄 DRAFT COMPLETE — PENDING DS SIGN-OFF. `03_DECISIONS/ADR-0029_t4-sub-band-architecture.md` (804 lines). Full 11-sub-band taxonomy, three-layer architecture, Kelly derivations, EXP prerequisites, budget partitioning, ADR amendments, governance gaps. Sign-off checklist attached. |
| **GG-038 REGISTERED** | ✅ T4 kill switch SLA ≤5s requirement — Phase 8 prerequisite; HIGH severity. |
| **GG-039 REGISTERED** | ✅ T4 price cache / staleness check architecture — Phase 8 prerequisite; MEDIUM severity. |
| **GG-040 REGISTERED** | ✅ T4 real-time data sources (live box score ≤2s, lineups ≤5s, Kalshi tick feed) — Phase 8 prerequisite; HIGH severity pre-Phase 8, LOW now. |
| **DECISION_LOG updated** | ✅ SESSION 66 entry written per CLAUDE.md rule 7. All strategic decisions logged. |
| **MEMORY_BANK.md updated** | ✅ Last reviewed updated to SESSION 66. |
| **TODO_NEXT.md updated** | ✅ SESSION 66 block added; T-179 marked DRAFT COMPLETE; T-180 registered (post-sign-off code implementation). |
| **PLAN.md updated** | ✅ Last reviewed updated to SESSION 66. |

---

## ONE THING PENDING

**ADR-0029 is DRAFT — it needs DS sign-off before any code changes can proceed.**

The sign-off checklist is the last section of `03_DECISIONS/ADR-0029_t4-sub-band-architecture.md` (20 items). DS reviews and signs. Once signed, T-180 executes the code changes to `execution_bands.py` (split T4_IN_PLAY into 11 sub-bands).

**Also still pending:** ADR-0028 Mods 5+9 sign-off (T-148). Both ADR-0028 and ADR-0029 await DS sign-off simultaneously. They are independent — ADR-0028 G6 scope (T1 Mods 5+9) and ADR-0029 Phase 8 T4 architecture. ADR-0028 sign-off no longer depends on ADR-0029 (T4 Activation Gate placeholder in ADR-0028 is completed by ADR-0029; both should be signed together or ADR-0028 first).

---

## Current Paper Portfolio

- Bankroll: **$751.10** (−24.9% from $1,000 initial; **drawdown kill switch is active — book halted**)
- Open: 0 bets ($0.00 deployed)
- Closed/Resolved: 158 bets | G6 gate: 158/30 (count PASSED; P&L FAILING — kill switch active)
- P&L: **−$248.90** (realized); G6 positive P&L gate: FAILING

---

## Active Cron on VPS (157.230.91.33)

```
DARK PERIOD — No active NBA games
Cron dormant; MLB pipeline not yet built
VPS HEAD: 97e66ae
```

---

## Key Constraints to Remember

1. G6 BLOCKER: No live capital — drawdown kill switch active at 25.12%; P&L gate FAILING
2. G6 BLOCKER: GG-004/GG-037 — model edge is anti-predictive vs Kalshi price (edge>0 winrate 0.356); alpha undemonstrated; deferred to EXP-017 at MLB scale → T-177
3. ADR-0028 AND ADR-0029 both PENDING DS SIGN-OFF — no code changes to either T4 band architecture or T1 Tier 2 promotion thresholds until signed
4. T4 code changes (T-180): BLOCKED until ADR-0029 sign-off
5. EXP-017 at scale (MLB + NBA regular season) is the commercial validation path — no verdict available until adequate sample collected per ADR-0024 (n≥500 unique markets)

---

## ⚙️ DECISION AUDIT

**Governance scan:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → **CLEAN** (no matches)

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| ADR-0029 (new) | N/A — ADR format, no decisions_logged field | SESSION 66 entry written | ✅ |
| GOVERNANCE_GAP_LOG (amended: GG-038/039/040) | N/A | No separate log entry needed (gaps are the record) | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260622_1300.md.
#   Primary pending: DS sign-off on ADR-0029 (03_DECISIONS/ADR-0029_t4-sub-band-architecture.md,
#   sign-off checklist is the last section) and ADR-0028 (Mods 5+9).
#   Once ADR-0029 is signed, execute T-180: split T4_IN_PLAY in execution_bands.py."
```
