# Session Handoff — 2026-06-01 SESSION 7 (Throughput Analysis)

**Trigger:** Operator-initiated session end / new context window
**Last commit:** `7307503` (main) — pushed to GitHub + VPS ✅
**VPS HEAD:** 7307503 — confirmed via git pull, fast-forward clean

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 581/581 passing (no code changes this session — docs + governance only)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; HEAD=7307503 ✅ FULLY DEPLOYED
- **Paper bets:** 0/66 resolved — G6 gate (APR-0017)
- **Portfolio:** CLEAN SLATE — $1,000 starting bankroll; `paper_portfolio.json` does NOT exist on VPS; cron creates it at Finals G1 Jun 3

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **KI-021 CLEARED** — sklearn 1.4.2 (train) vs 1.8.0 (VPS inference) gap is non-material | Direct probability comparison: 205 vectors; max_abs_delta=0.00106 (<0.1%); zero cases crossing MIN_EDGE; zero bet direction flips. Registered LOW severity; resolve at T-072 (pin sklearn==1.4.2 at model refresh). | `10_INFRA_OPERATIONS/KNOWN_ISSUES.md` KI-021; DECISION_LOG KI-021 entry | EL |
| **DESIGN THROUGHPUT INVARIANT permanently locked** — bot design intent is hundreds to thousands of bets per game night; 66-bet G6 floor is non-binding; binding constraints are EXP-017 Part B + ≥5 game nights | Corrective decision after operator correction. Framing was repeatedly lost across 20+ sessions. Locked into CLAUDE.md (new "Design throughput" section), MEMORY_BANK.md (invariant #11), APR-0017 (floor note), DECISION_LOG (invariant entry). | `CLAUDE.md` "Design throughput — do not dismiss this"; `MEMORY_BANK.md` invariant #11; `DECISION_LOG.md` DESIGN THROUGHPUT INVARIANT entry | DS |
| **KI-022 REGISTERED; T-115 CREATED** — `run_paper_trade.py:290` evaluates 1-of-~7-8 available Kalshi thresholds per player; suppresses ~7-8× market depth vs. design intent | 38 markets / 5 players = 7.6 thresholds/player available on Kalshi for Finals game. Bot selects one (closest to pts_mean). At all-thresholds behavior: regular season yields 25-40 T1 bets/game; at full design (T1-T4, multi-stat, multi-venue): 500-900 bets/game, 7,500-13,500 bets/night. Must resolve before 2026-27 regular season — G6 accumulation depends on it. ~15-line change. | `10_INFRA_OPERATIONS/KNOWN_ISSUES.md` KI-022; `04_EXECUTION/TODO_NEXT.md` T-115; `DECISION_LOG.md` THROUGHPUT ANALYSIS entry | EL/DS |
| **T-109 dry-run PASS** — SCP connectivity to VPS confirmed; clean fail on missing portfolio (expected post-reset) | `run_resolve_local.py` exits 1 on missing `paper_portfolio.json` — not silent. This is correct: VPS intentionally has no file until cron fires Jun 3. Real T-109 run after Finals G1 will succeed. | T-109 standing procedure | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Session-start governance protocol | ✅ All 3 steps + ARE WE COMPROMISED? Q1-Q7 run. GG-004 OPEN, 5 stubs (all known). |
| VPS sync verification | ✅ Docs-only delta confirmed; no code divergence. |
| KI-021: sklearn gap investigation | ✅ Cleared. 205-vector comparison. Max delta 0.00106. Zero direction flips. LOW severity. |
| Design throughput invariant lock | ✅ Written to CLAUDE.md, MEMORY_BANK.md, APR-0017, DECISION_LOG. |
| Throughput analysis from first principles | ✅ Cohort=75 players; ~7-8 Kalshi thresholds/player/game; build-up table: 3-10 bets (current) → 500-900 bets (full design) per regular season game. |
| KI-022 registered | ✅ Single-threshold bottleneck documented. Severity=MEDIUM. Gate: must resolve before 2026-27. |
| T-115 created | ✅ `TODO_NEXT.md` entry: ~15-line change to loop all thresholds instead of min(). |
| DECISION_LOG entry (throughput analysis) | ✅ Full build-up table + KI-022 + T-115 logged. |
| VPS push | ✅ 3 commits pushed (c084c82, b526484, 7307503). Fast-forward clean. |
| T-109 dry-run | ✅ PASS — SCP connectivity confirmed; clean exit(1) on missing portfolio as expected. |
| MEMORY_BANK.md update | ✅ Last reviewed, last milestone, active risks, portfolio state all updated. |

---

## OPEN ITEMS — Carry to Next Session

| Priority | Item | Notes |
|----------|------|-------|
| HIGH — Jun 3 | **Run T-109 after Finals G1** | (1) `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py` (2) `PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio` — cron creates portfolio Jun 3; T-109 runs after resolution |
| HIGH — before 2026-27 | **T-115: evaluate all thresholds per player** | `run_paper_trade.py:290` change `min(player_mkts, ...)` → loop. ~15 lines. G6 accumulation depends on this. |
| MEDIUM — dark period | **T-072: model retrain before 2026-10-01** | sklearn pin to 1.4.2 at this point. New ADR required per ADR-0004. |
| MEDIUM | **T-093–T-099: documentation debt** | 7 docs with `decisions_logged: false`. Non-blocking; dark period work. |
| LOW | **T-107: Polymarket NBA tag (KI-019)** | Confirm before T-077 activation. |

---

## Current Paper Portfolio

- **Bankroll:** $1,000.00 (clean slate — INVALIDATED portfolio discarded)
- **Open bets:** 0 — portfolio file does not exist on VPS yet
- **Resolved bets:** 0/66 (APR-0017 G6 floor)
- **G6 counter:** 0/66
- **Prior portfolio:** `.INVALIDATED_20260601.json` on VPS — inadmissible as G6 evidence

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

Finals G1 (NYK vs SAS, Jun 3): cron will create `paper_portfolio.json` on first run, evaluate cohort players (75 total; ~38 KXNBAPTS markets expected), submit bets at T1 window.

---

## Key Constraints

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**APR-0017**: ≥66 resolved bets + ≥5 game nights + full four-tier evidence — GG-004 OPEN)
3. `arb/` folder = REFERENCE ONLY — do not incorporate until APR-0010 signed
4. No automated retraining in production — frozen model policy
5. EXP-017 Part B n=2; do not cite as commercial validation until ≥66 floor met
6. **T-115 is a G6 prerequisite** — without it, regular season yields ~3-10 bets/game; 66-bet floor takes ~8-20 game nights. With it: 1-2 game nights.

---

## ⚙️ DECISION AUDIT

All decisions made this session written to `DECISION_LOG.md` inline (not deferred to session end).

| Decision | DECISION_LOG entry | Written |
|----------|-------------------|---------|
| KI-021 clearance (sklearn gap) | ✅ | Inline |
| Design throughput invariant | ✅ | Inline |
| Throughput analysis + KI-022 + T-115 | ✅ | Inline |

7 legacy `decisions_logged: false` docs (T-093–T-099) unchanged — dark period work.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude:
# "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260601_THROUGHPUT.md.
# VPS is at 7307503. Portfolio is clean slate — no paper_portfolio.json exists until cron fires Jun 3.
# Priority: (1) confirm Finals G1 Jun 3 has played, (2) run T-109 standing procedure,
# (3) check EXP-017 Part B result for n-update, (4) assess T-115 readiness."
```

---

## Next Session Primer

```
NEXT SESSION PRIMER:
VPS HEAD=7307503 (deployed 2026-06-01 SESSION 7; 581/581 tests passing; bot armed for Finals G1 Jun 3).
Portfolio is CLEAN SLATE ($1,000; no paper_portfolio.json; cron creates it Jun 3).
After Finals G1 Jun 3, run T-109: (1) run_resolve_local.py, (2) fetch_kalshi_prices.py --portfolio.
G6 gate = APR-0017 (≥66 bets, ≥5 game nights, four tiers). GG-004 OPEN (n=2 EXP-017 Part B).
KEY: T-115 (evaluate all thresholds per player, not just closest) is a G6 prerequisite — 
without it, ~3-10 bets/game; with it, ~25-40 bets/game from T1 alone.
Dark period (Jun-Oct 2026): T-115, T2/T3 production-readiness, model retrain, EXP-017 Part B accumulation.
```
