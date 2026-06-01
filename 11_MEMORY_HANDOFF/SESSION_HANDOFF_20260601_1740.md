# Session Handoff — 2026-06-01T17:40Z

**Trigger:** Context window near limit (operator-initiated)
**Last commit:** `16116bb` (main) — local only; NOT YET PUSHED TO VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 581/581 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; **⚠️ VPS IS 4+ COMMITS BEHIND LOCAL**
- **Paper bets:** 0/66 resolved — G6 gate (APR-0017; new floor is ≥66, not 30)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **APR-0017 ACCEPTED** (supersedes APR-0016) — Four-tier multi-dimensional G6 evidence standard. All criteria expressed as rates/slopes/proportions; derived numeric floors only. ≥66 resolved bets (from power formula) + ≥5 game nights (from slope regression df). | APR-0016 "30 resolved bets" was structurally blind to calibration failure, demo-price contamination, single-night variance, and execution bugs. Count-as-proxy fails all broken-system tests. GG-005 documented the failure. | `00_ADMIN/APR-0017_g6-multi-dimensional-evidence-standard.md` + DECISION_LOG T-113 v2 entry | PO/DS (Earl) |
| **GG-005 RESOLVED** — APR-0016 structural rework complete. APR-0017 is the operative G6 gate. | APR-0016 flagged 2026-05-31; remediation T-113 complete; sign-off received 2026-06-01. | `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | PO |
| **EXP-017 Part B live mode built and run (T-105)** — n=2 unique resolved markets (Fox YES WIN, SGA NO LOSS). Per-unique-market EV = +$0.01/bet. DIRECTIONAL_POSITIVE. GG-004 OPEN (floor is ≥66). | Historical prices contaminated (in-play); candlestick API returns 404. VPS pre-game log files (`pregame_*.json`) are the correct source — captured at T1 cron alongside model p_estimates. | `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` T-105 entry; `exp_output/EXP-017/EXP-017_results.json` | EL |
| **Price timing finding** — SGA market moved 0.49 → 0.57 between first portfolio execution (17:40 UTC) and T1 cron (21:30 UTC May 29). At actual execution price, edge_vs_market = -0.014 (below MIN_EDGE=0.02). Pre-ADR-0006 artifact. Clean G6 evidence (Finals G1 onward) uses T1 cron prices throughout. | Bot placed bet at earlier price before T1 cron ran. ADR-0006 eliminates this going forward — bets only placed at T1 cron time using T1 cron prices. | DECISION_LOG T-105 entry | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-113: APR-0017 v2 design + sign-off | ✅ APR-0017 ACCEPTED 2026-06-01. No arbitrary count thresholds. All criteria rate/slope/proportion. Derived floors: ≥66 bets, ≥5 nights. GG-005 RESOLVED. |
| T-113: Governance artifacts updated | ✅ APR-0017 file created; APPROVALS_REGISTER updated; GOVERNANCE_GAP_LOG GG-005 → RESOLVED; DECISION_LOG entry added |
| T-105: EXP-017 Part B live mode | ✅ `--from-pregame DIR --portfolio PATH` mode added to `run_exp017.py`. Loads VPS pregame JSON files, joins on kalshi_ticker, computes EV vs actual Kalshi mid prices. |
| T-105: fetch_kalshi_prices.py (T-109 tool) | ✅ New file at `src/prediction_market_bot/fetch_kalshi_prices.py`. Syncs pregame_*.json from VPS to local `exp_output/EXP-017/`. Flags: `--portfolio`, `--run-exp017`, `--force`. |
| T-105: First EXP-017 Part B run | ✅ n=2 unique markets. Per-unique EV=+$0.01/bet. All_positions EV=+$0.04/bet. DIRECTIONAL_POSITIVE but far below ≥66 floor. GG-004 OPEN. |
| T-105: VPS pregame files committed | ✅ `exp_output/EXP-017/pregame_20260529.json`, `pregame_20260530.json`, `pregame_20260531.json` + `paper_portfolio_invalidated.json` committed. |
| MEMORY_BANK.md update | ✅ Current State Snapshot updated (tests=581, APR-0017, GG-005 RESOLVED, VPS deploy needed, 3 open bets); invariant #8 rewritten for APR-0017 |
| PLAN.md update | ✅ Last reviewed date + Phase 6 deliverables table updated |

---

## ONE THING PENDING

**VPS deploy before Finals G1 (Jun 3, ~22:00 UTC).**

The VPS is running commit 92539b9 (may also be at 16116bb if a previous session pushed). Local is at `16116bb` with APR-0017 artifacts, EXP-017 Part B code, and fetch_kalshi_prices.py. Without the deploy, the T1 cron on Jun 3 will run old code and the fetch procedure won't be available.

```bash
ssh root@157.230.91.33 "cd /opt/prediction-market-bot && git pull"
```

Then verify: `ssh root@157.230.91.33 "cd /opt/prediction-market-bot && git log --oneline -3"`

After Finals G1 resolves, run T-109 standing procedure:
```bash
# 1. Resolve positions
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py

# 2. Sync pregame files from VPS
PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio

# 3. (Re-run EXP-017 only when ≥66 markets accumulated — currently n=2)
```

---

## Current Paper Portfolio

- Bankroll: $683.41 (32% drawdown from prior invalidated bets — APR-0016 reset; prior portfolio `paper_portfolio_invalidated.json`)
- Open (Finals G1 Jun 3): KAT YES (mid=0.375) | Anunoby NO (mid=0.61) | Brunson NO (mid=0.545)
- Closed/Resolved: 0 clean G6 bets | G6 gate: 0/66 (APR-0017)
- Prior invalidated bets: 6 closed (Fox 3×WIN + SGA 3×LOSS) — NOT counted; placed on pre-ADR-0006 system

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
2. No live capital until G6 (**APR-0017**: ≥66 resolved bets + ≥5 game nights + full four-tier evidence — GG-004 still OPEN)
3. `arb/` folder = REFERENCE ONLY — do not incorporate until APR-0010 signed
4. No automated retraining in production — frozen model policy
5. EXP-017 Part B result is DIRECTIONAL_POSITIVE but n=2; do not cite as commercial validation until ≥66 floor met

---

## ⚙️ DECISION AUDIT

**Governance scan result:** 7 documents with `decisions_logged: false` — none modified this session; T-093–T-099 registered in prior sessions.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| APR-0017 (new) | N/A (new approval doc, not a `decisions_logged` doc) | T-113 v2 entry written | ✅ |
| GOVERNANCE_GAP_LOG.md | N/A | GG-005 resolved inline | ✅ |
| DECISION_LOG.md | N/A | T-113 + T-105 entries written | ✅ |
| 7 legacy `decisions_logged: false` docs | false | T-093–T-099 registered (prior session) | ✅ T-NNN registered |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260601_1740.md.
# Priority: (1) confirm VPS deploy status, (2) check if Finals G1 Jun 3 has resolved,
# (3) run T-109 standing procedure if game resolved."
```

---

## Next Session Primer

```
NEXT SESSION PRIMER:
VPS must be deployed before Finals G1 (Jun 3, ~22:00 UTC): ssh root@157.230.91.33 "cd /opt/prediction-market-bot && git pull". After each Finals game, run the T-109 standing procedure: (1) run_resolve_local.py, (2) fetch_kalshi_prices.py --portfolio, (3) re-run EXP-017 when ≥66 markets accumulated. G6 gate is now APR-0017 (≥66 bets, ≥5 game nights); commercial validation (GG-004) is OPEN and DIRECTIONAL_POSITIVE at n=2.
```
