# Session Handoff — 2026-07-03T12:30Z

**Trigger:** Context window near limit (SESSION 117 continuation) — operator noted usage credits, requested finish-and-close.
**Last commit:** `4da1f87` (main) — pushed to GitHub + VPS, both fast-forwarded, clean.

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** unchanged this session (docs-only edits) — last known 2293+ passing / 7 skipped / 1 pre-existing unrelated failure
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — `t4-mlb` systemd active, MLB crons running
- **Paper bets:** MLB 49/30 resolved (G6 met on count, EV/DS sign-off/EXP-017 still pending); NBA 158/30 resolved but DARK/FROZEN, not counted toward active gate

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **ADR-0040 (Kelly de-rating 0.25→0.14) is PROPOSED, NOT ACCEPTED.** No `risk.py` change made. | GG-071 ruin-risk finding (T1 MLB, real 53% edge, still 46%/1yr chance of tripping the 20% drawdown kill switch under compounding). Recreated MC (`scripts/mc_forward_projection.py`) + sensitivity sweep back the recommendation, but Hard Rule 3 requires explicit operator sign-off before any live parameter edit. | `03_DECISIONS/ADR-0040_ruin-risk-remediation-kelly-derating-proposed.md`; GG-071 in GOVERNANCE_GAP_LOG.md; T-223 in TODO_NEXT.md | Earl (pending) |
| **Governance-record correction:** a T-233/T-223 task-number conflation (introduced by this session's own earlier edits) was found and fixed across `MEMORY_BANK.md` (5 spots) and `PLAN.md` (1 spot). | Two concurrent sessions were both working GG-071-adjacent problems the same day with similarly-named files; superficial similarity caused mislabeling. Ground truth established via the file's own docstring, TODO_NEXT.md's pre-existing T-223 row, and a HEAD-vs-working-tree diff of the real T-233 entry. | DECISION_LOG.md Notable Judgment Calls entry, 2026-07-03 ("[Governance-record correction]") | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-231 | ✅ CLOSED — C8 Panel 6 (T4 MLB Detail) deployed to VPS; live re-entry verification remains open pending a live game |
| T-230 | ✅ Severity corrected LOW→MEDIUM (10 real positions in re-fire-tracking gap); fix deferred, left queued per Earl's explicit choice |
| GG-004/EXP-017 (Item 1) | ✅ Run against real MLB data (n=49): DIRECTIONAL_POSITIVE, EV=+$2.04/bet, win 53.1%; GG-004 stays OPEN (below ADR-0024 floors); GG-077 registered (production-side `fee_net_edge` sign-convention finding, unfixed, flagged for review) |
| T-223 / ADR-0040 | ✅ Review complete, proposal drafted — **PROPOSED, awaiting Earl's sign-off** |
| Governance correction | ✅ T-233/T-223 mislabeling found and fixed in MEMORY_BANK.md, PLAN.md, DECISION_LOG.md, TODO_NEXT.md |

---

## ONE THING PENDING

**ADR-0040 needs Earl's explicit decision (accept / reject / amend).** It is fully drafted at `03_DECISIONS/ADR-0040_ruin-risk-remediation-kelly-derating-proposed.md`. If accepted: edit `risk.py`'s `DEFAULT_KELLY_FRACTION` 0.25→0.14, update `scripts/run_monte_carlo.py`'s `DEFAULT_T1_KELLY`, update tests asserting the literal 0.25, then re-run `mc_forward_projection.py` to confirm the realized effective stake fraction lands in the 0.62-0.71% target range. No code has been touched — this is purely a decision, not an in-flight task.

Secondary, lower-priority open item: T-231's live re-entry verification (GG-076 fix) still needs a check once a live MLB game is actually running — `t4-mlb` is active with the fix loaded but had zero cycles at last check.

---

## Current Paper Portfolio

- **MLB (ACTIVE):** Bankroll $926.12 | Open 14 ($173.88 deployed) | Resolved 49/30 (G6 count met, EV/DS sign-off pending) | Realized drawdown 0.0% | P&L +$100.00
- **NBA (DARK/FROZEN):** Bankroll $751.10 | Open 0 | Resolved 158/30 | Drawdown 24.9% (historical, not live risk) | P&L -$248.90

---

## Key Constraints to Remember

1. No live capital until G6 (30 resolved paper bets + positive P&L + EXP-017 commercial validation + DS sign-off) — MLB has cleared the count floor but not the EV/DS floors.
2. ADRs are immutable once accepted; ADR-0040 is still PROPOSED — do not treat its 0.14 figure as decided in any future session.
3. This project has multiple concurrent/parallel sessions editing the same navigation files (MEMORY_BANK.md, PLAN.md, DECISION_LOG.md) — cross-reference primary sources (file docstrings, existing task registrations) before trusting an inherited narrative about "what task X's deliverable is," per this session's own governance-correction finding.

---

## ⚙️ DECISION AUDIT

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| ADR-0040 | N/A (ADR, not a `decisions_logged` doc) | ADR Index row + Notable Judgment Calls row, both added | ✅ |
| MEMORY_BANK.md / PLAN.md corrections | N/A | Governance-correction entry in DECISION_LOG.md | ✅ |

Governance scan (Step 0) at session start: clean — no `decisions_logged: false` documents found.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260703_1230.md.
# ADR-0040 is awaiting Earl's accept/reject/amend decision — check if that's happened before
# touching risk.py. Otherwise resume the priority queue in TODO_NEXT.md."
```
