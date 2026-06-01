# Session Handoff — 2026-06-01T14:00Z

**Trigger:** Operator-initiated session end  
**Last commit:** `5e624ea` (main) — governance docs only; VPS deploy not required (no code changes)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 589/589 passing (VPS) — no code changes this session
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; git HEAD = 5e624ea (3 commits ahead of prior session's 710e8bf)
- **Paper bets:** 0/66 resolved — G6 gate (APR-0017 floor; clean slate; Finals G1 Jun 3 is first eligible game)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GG-006 SUBSTANTIALLY RESOLVED: Kalshi position accountability limits are per-contract (in contract Terms and Conditions), NOT in the main DCM Rulebook body | DCM Rulebook v1.26 and DCO Rulebook v1.4 read in full (82pp + 108pp). PALs and Position Limits are defined as dollar-loss amounts; exact values are in each contract's individual Terms and Conditions on Kalshi's website — not in the main PDF. DCO Rule 7.5 (Fully Collateralized Positions) is the binding structural constraint: clearing house will not accept positions exceeding deposited funds. Account balance ($683.41) is the effective position ceiling at current scale. | `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-006 updated to SUBSTANTIALLY RESOLVED); `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` (entry added) | DS |
| T-117 registered: verify KXNBAPTS contract-specific Terms page before G6 live capital authorization | One item remains from GG-006: the specific PAL and Position Limit numbers for KXNBAPTS (NBA player points) contracts are on the contract's Terms and Conditions page on Kalshi's website — not in the main rulebook. Required before ADR-0005 draft. LOW risk at current bankroll ($10–80/bet). | `04_EXECUTION/TODO_NEXT.md` (T-117 added) | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| GG-006 rulebook review (DCM v1.26 + DCO v1.4) | ✅ Both rulebooks read in full. Position accountability framework fully understood. GG-006 status updated from "OPEN (partially de-risked)" → "SUBSTANTIALLY RESOLVED — pending contract Terms verification." |
| GOVERNANCE_GAP_LOG.md updated | ✅ GG-006 entry expanded with: rulebook review findings, PAL/Position Limit definitions (dollar-loss denominated), Rule 5.18/5.19/5.4 key provisions, DCO Rule 7.5 Fully Collateralized finding, remaining open item (KXNBAPTS contract Terms page). |
| DECISION_LOG.md updated | ✅ New entry added: GG-006 SUBSTANTIALLY RESOLVED — full rulebook findings documented. Header updated to SESSION 9. |
| MEMORY_BANK.md updated | ✅ GG-006 active risk entry updated from OPEN to SUBSTANTIALLY RESOLVED with full findings summary. Header updated to SESSION 9. |
| TODO_NEXT.md updated | ✅ Header updated. T-117 registered: verify KXNBAPTS contract Terms page (dark period, LOW priority). |
| PLAN.md updated | ✅ Header date updated to SESSION 9. |

**Files modified:** `03_DECISIONS/GOVERNANCE_GAP_LOG.md`, `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`, `11_MEMORY_HANDOFF/MEMORY_BANK.md`, `04_EXECUTION/TODO_NEXT.md`, `04_EXECUTION/PLAN.md`  
**Files NOT modified:** All src/ code — no code changes this session  
**Test count:** 589/589 (unchanged)

---

## ONE THING PENDING

**T-109: Run resolution + EXP-017 data collection after Finals G1 (Jun 3).**

State: Finals G1 fires Jun 3 (NYK vs SAS). VPS cron is armed and will auto-place paper bets at PIPE-03 (22:00 UTC + 01:30 UTC). Resolution cannot run on VPS (403 block on nba_api). After the Jun 3 game concludes and nba_api updates (~Jun 4 morning ET):

```bash
# Step 1: Resolve paper bets locally
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py

# Step 2: Fetch pregame prices from VPS for EXP-017 Part B
PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio

# Step 3: Re-run EXP-017 Part B (only after ≥66 markets accumulated)
# PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py --from-pregame logs/pregame/ --portfolio logs/paper_portfolio.json
```

Repeat steps 1–2 after each Finals game. Step 3 triggers when APR-0017 floor (≥66 resolved markets) is met — which requires regular season (one Finals game ≈ 7–15 bets at current cohort size).

---

## Current Paper Portfolio

- **Bankroll:** $1,000.00 (clean slate; pre-ADR-0006 bets invalidated 2026-05-31)
- **Open:** 0 (paper_portfolio.json does not exist on VPS; cron creates it at Finals G1 Jun 3)
- **Closed/Resolved:** 0 | G6 gate: 0/66 resolved markets (APR-0017 statistical floor)
- **G6 status:** Waiting for Finals G1 Jun 3 to begin clean evidence accumulation

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
2. No live capital until G6 (APR-0017: ≥66 resolved markets + ≥5 game nights + EXP-017 Part B CONFIRMED + Tier 0–3 all passing)
3. EXP-017 Part B is at n=2, DIRECTIONAL_POSITIVE — GG-004 remains OPEN until ≥66 markets
4. GG-006: one item remains before G6 ADR-0005 — check KXNBAPTS contract Terms page on Kalshi for PAL/Position Limit numbers (T-117)
5. VPS resolution is blocked (403 on nba_api) — always run run_resolve_local.py from local machine after each game

---

## ⚙️ DECISION AUDIT

**Governance scan result:** 7 documents with `decisions_logged: false` — all have pre-existing T-NNN tasks (T-093–T-099). None were modified this session. No new governance debt created.

| Document | decisions_logged | DECISION_LOG entries written | Status |
|----------|-----------------|------------------------------|--------|
| GOVERNANCE_GAP_LOG.md | N/A (not a `decisions_logged` document) | GG-006 rulebook finding logged | ✅ |
| DECISION_LOG.md | N/A | New entry: GG-006 SUBSTANTIALLY RESOLVED | ✅ |
| EXECUTION_ARCHITECTURE.md | false | Not modified this session | ✅ T-093 registered |
| MONITORING_DRIFT_PLAN.md | false | Not modified this session | ✅ T-094 registered |
| METHODOLOGY.md | false | Not modified this session | ✅ T-095 registered |
| VENUE_REGISTRY.md | false | Not modified this session | ✅ T-096 registered |
| RISK_APPETITE_CONSTRAINTS.md | false | Not modified this session | ✅ T-097 registered |
| QUALITATIVE_SIGNALS.md | false | Not modified this session | ✅ T-098 registered |
| ROADMAP_MILESTONES.md | false | Not modified this session | ✅ T-099 registered |

---

## Open Governance Items at Session End

| ID | Status | Description |
|----|--------|-------------|
| GG-004 | OPEN | EXP-017 Part B n=2, DIRECTIONAL_POSITIVE — blocks G6 Tier 0; floor ≥66 markets |
| GG-006 | SUBSTANTIALLY RESOLVED | Position accountability framework understood; T-117 is the remaining verification |
| KI-017 | OPEN | EV validated against 0.50 null, not Kalshi prices — addressed by EXP-017 |
| KI-018 | OPEN | max_daily_loss_usd: 1000 inactive at current bankroll; drawdown % is operative kill switch |
| KI-019 | OPEN | Polymarket "tag": "nba" unconfirmed; silent empty return risk at T-077 |
| KI-023 | OPEN | KXNBAPTS market depth unknown; bot order flow may move own prices at full scale |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260601_1400.md, 589 tests on VPS, Finals G1 Jun 3 is next game"
```
