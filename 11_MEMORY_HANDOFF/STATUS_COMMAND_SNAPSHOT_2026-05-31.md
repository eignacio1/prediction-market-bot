> **HISTORICAL — archived 2026-10-09.** This was the body of `.claude/commands/status.md` until the strategic window's forest pass replaced it with a pointer-based version. It describes the project as of late May 2026. Do not use it for current state.

# /status — Quick Project Status Check

Read `11_MEMORY_HANDOFF/MEMORY_BANK.md`, `04_EXECUTION/TODO_NEXT.md`, and `02_ARCHITECTURE_DESIGN/STRATEGY_OVERVIEW.md` (Section 3 comparison matrix and activation roadmap only). Then provide a concise status report in this exact format:

---

**PHASE:** [current phase]
**LAST GATE:** [gate name + date]
**NEXT GATE:** [gate name + what's required]

**COMPLETED SINCE LAST SESSION:**
- [bullet each completed task with T-number]

**IN PROGRESS:**
- [bullet each in-progress task with owner + blocker if any]

**NEXT 3 ACTIONS (in priority order):**
1. [T-number + specific action]
2. [T-number + specific action]
3. [T-number + specific action]

**BLOCKERS:**
- [any hard blockers with ETA]

**RISKS TO WATCH:**
- [any risks that could affect the next gate]

**MODEL STATUS:**
- Version: [from models/prod_model_meta.json]
- Age: [days since trained_at]
- Staleness flag: [>30 days = WARNING]

**STRATEGY STATUS:**
- Active strategies: [A/G/H — paper; which bands T1/T2/T3 running]
- Next to activate: [strategy + gate required]
- Blocked: [strategies blocked + what unblocks them]

**EXECUTION BAND STATUS:**
- T1 (PIPE-02): [cron confirmed / last run date]
- T2 (PIPE-05): [skeleton / DS-04 pending]
- T3 (PIPE-06): [cron deployed / last run date]
- T4/T5: [BLOCKED — Phase 8+]

**VENUE STATUS:**
- Active venues: [from VENUE_ROUTER_MODE env var]
- Polymarket: [T-077 status]

**TEST STATUS:**
- Run `python -m pytest tests/ -q` and report pass/fail count

---

Do not add commentary or recommendations beyond what was explicitly requested. Facts only.
