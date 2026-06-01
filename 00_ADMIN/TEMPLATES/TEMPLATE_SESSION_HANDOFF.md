# Session Handoff — YYYY-MM-DDTHH:MMZ

**Trigger:** [Context window near limit / clean cutover / operator-initiated]
**Last commit:** `[hash]` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** [e.g., 6/7 ACTIVE]
- **Tests:** [N/N passing]
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron [running / not running]
- **Paper bets:** [N/30 resolved] — G6 gate

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

*This section is MANDATORY. Judgment calls, threshold changes, sequencing pivots, and holistic review outcomes belong here — not just in the task list. If a decision was made verbally during this session and is not recorded here, it will be lost across context windows.*

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| [What was decided] | [Why — the constraint, deadline, or stakeholder driver] | [Which file now holds the authoritative record] | DS |

*If no strategic decisions were made this session, write: "None — session was implementation-only."*

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| [Task ID / description] | ✅ [outcome] |

---

## ONE THING PENDING (if any)

[What is the single most important thing the next session must know to continue?]

**Precision standard for in-flight work:** Do not write "experiment pending (~15 min)." Write the exact current state:
- Is data already pulled? → "Cache exists at exp_output/EXP-NNN/. Run with `SKIP_PULL=1` — completes in <2 min."
- Is a process still running? → "Script launched at HH:MM UTC. Output at exp_output/EXP-NNN/. Expected done by HH:MM UTC."
- Is it waiting on operator? → "Waiting for [specific operator action] at [specific URL or path]. Infrastructure is ready."

Ambiguous state descriptions are the most common source of wasted time in the next session.

---

## Current Paper Portfolio

- Bankroll: $[amount] ([N]% drawdown from [N] open bets)
- Open: [list]
- Closed/Resolved: [N] | G6 gate: [N]/30

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016)
3. [Any session-specific constraint]

---

## ⚙️ DECISION AUDIT (Required at Sprint Close — Skip for Mid-Sprint Handoffs)

*Complete when closing a sprint, phase gate, or any session that created/modified a strategic document.*

**Step 1:** Run `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null`

**Step 2:** For each document created or substantially modified this session:

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| [filename] | true / false | [entry IDs or "none needed"] | ✅ / ❌ need T-NNN |

*Sprint is NOT closed if any row shows `false` without a corresponding T-NNN registered in TODO_NEXT.md.*

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_[YYYYMMDD_HHMM].md, confirm [N] tests"
```
