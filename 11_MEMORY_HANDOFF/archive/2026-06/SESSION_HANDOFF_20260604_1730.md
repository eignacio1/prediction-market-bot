# Session Handoff — 2026-06-04T17:30 PDT (00:30 UTC Jun 5)

**Trigger:** Context window near limit — operator-initiated /session-end  
**Last commit:** `25dcb7c` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 715/715 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; PIPE-02 BOT_C4_ACTIVE guard removed (GG-012 fix live)
- **Paper bets:** 9 open (Finals G2, game_date=2026-06-05) | 0 resolved | G6 gate requires ≥66 resolved bets + ≥5 nights + EXP-017 Part B CONFIRMED

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| PIPE-02 `BOT_C4_ACTIVE` guard removed entirely | PIPE-02 is read-only (writes pregame JSON and team_stats_cache; never places orders). Blocking it on C4 activation state caused 2 silent cron failures and ADR-0015 adj_λ was never applied. The guard was architecturally incorrect from the moment BOT_C4_ACTIVE was permanently set in .env. | DECISION_LOG.md SESSION 31 / GG-012 entry; commit 2997c71 | DS |
| G2 Monte Carlo uses portfolio-based Bernoulli draws, not Poisson re-simulation | pregame_20260604.json doesn't exist (PIPE-02 failed). Using stored `model_p` values from paper_portfolio.json is more accurate than re-running from scratch — it uses the actual probabilities at bet placement time. | SESSION 31 MC analysis (inline, no separate file) | DS |
| EXP-018 G2 data tests UNADJUSTED Poisson, not ADR-0015 | GG-012 means no PIPE-02 succeeded before G2 PIPE-03 run. adj_λ never applied to G2 bets. EXP-018 G2 results measure baseline Poisson vs. Kalshi prices. ADR-0015 commercial validation deferred to Finals Game 3+ where PIPE-02 (now fixed) succeeds first. | DECISION_LOG.md SESSION 31 / GG-012 entry | DS |
| GAME_DATE = run date (not game date) design confirmed correct | PIPE-02 and PIPE-03 both run on June 4; cache files named by run date; positions labeled by game date via ticker parsing. The naming is intentional, not a bug. No action needed. | Timing sweep, SESSION 31 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-133 DECISION_LOG entry | ✅ fee_contaminated NO-direction false-positive bug governance entry. Commit 1b7ee83. |
| GG-012 diagnosed | ✅ Root cause: `run_pregame.py __main__` guard exits on BOT_C4_ACTIVE=true. Confirmed via pregame_cron.log (2× FATAL exits), absence of pregame_20260604.json, paper_early_cron.log `[TSS] Built fresh: 0/30 teams loaded`. |
| GG-012 fixed | ✅ Removed BOT_C4_ACTIVE guard from `run_pregame.py`. Updated docstring. Commit 2997c71. Deployed to VPS. 715/715 tests. |
| GG-012 governance artifacts | ✅ GOVERNANCE_GAP_LOG.md updated. DECISION_LOG entry committed (25dcb7c). T-134 registered. |
| Timing sweep | ✅ 5 timing properties analyzed: GAME_DATE design, PIPE-03R date format, idempotency by ticker, GAME_DATE_ISO as as_of_date, G2 resolution timeline. No functional bugs beyond GG-012. |
| G2 Monte Carlo | ✅ Portfolio-based, N=10,000, seed=42. EV=+$60.02 (+16.5% ROI), P(profit)=82.7%, kill-switch risk=0.11%. p5=-$31.18, p50=+$61.55, p95=+$137.64. Note: model_p values use unadjusted Poisson λ. |
| User timing error corrected | ✅ Confirmed G2 is June 5 (not "tonight" from June 4). G2 tips ~23:00 UTC Jun 5. PIPE-03R fires 06:00 UTC Jun 5 (before game → no-op). G2 resolves at 06:00 UTC Jun 6. |

---

## ONE THING PENDING

**T-134 — PIPE-03 TeamStatsStore size=0 alert.**

GG-012 was invisible for 2 consecutive cron cycles because when TSS builds fresh but loads 0 teams, PIPE-03 treats it as a graceful fallback to raw `pts_mean`. No warning, no audit event. Fix: add `logger.warning()` or audit ERROR in `run_paper_trade.py` when `len(team_store) == 0` after a fresh build attempt. This is the one remaining item that closes GG-012.

**Current state:** T-134 is registered but not implemented. Infrastructure is straightforward — 2–3 lines in `run_paper_trade.py` at the TeamStatsStore load/build path.

---

## Current Paper Portfolio

- Bankroll: $636.24 (36.4% drawdown from initial $1,000 — all from open positions, not realized losses)
- Open: 9 positions, all Finals G2 (game_date=2026-06-05)
  - Wembanyama NO 35+: $75.11, p_win=95.2%
  - Wembanyama NO 30+: $39.01, p_win=77.2%
  - Wembanyama NO 25+: $7.70, p_win=41.1%
  - Wembanyama YES 20+: $25.17, p_win=89.7%
  - Castle NO 25+: $12.12, p_win=88.4%
  - Castle YES 20+: $17.51, p_win=45.8%
  - Castle YES 15+: $49.93, p_win=86.0%
  - Castle YES 10+: $71.52, p_win=99.2%
  - Vassell NO 25+: $65.69, p_win=99.7%
- Closed/Resolved: 0 | G6 gate: 0/66 resolved bets
- G2 resolves: PIPE-03R 06:00 UTC June 6 (game tips ~23:00 UTC Jun 5)
- **ADJ-λ STATUS: NOT APPLIED to G2 bets (GG-012). Applied starting G3+ (PIPE-02 now fixed).**

---

## Active Cron on VPS (157.230.91.33)

```
21:55 UTC  — PIPE-02 inference (run_pregame.py) — BOT_C4_ACTIVE guard REMOVED
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:25 UTC  — PIPE-02 late (run_pregame.py)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
```

**Next cron events:**
- 01:25 UTC Jun 5 — PIPE-02 late (will now run with guard removed; but G2 tickers already open → PIPE-03 at 01:30 will skip all 9 via idempotency)
- 06:00 UTC Jun 5 — PIPE-03R fires before G2 tips → no-op (game not played yet)
- ~23:00 UTC Jun 5 — Finals Game 2 tips (NYK at SAS)
- 06:00 UTC Jun 6 — PIPE-03R resolves G2 positions

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (≥66 resolved bets + ≥5 game nights + EXP-017 Part B CONFIRMED — APR-0017)
3. G2 bets use UNADJUSTED Poisson λ. EXP-018 G2 results test baseline, not ADR-0015. First adj_λ evidence = Finals Game 3+.
4. GG-012 is PARTIALLY RESOLVED — code fixed, T-134 monitoring still open.

---

## ⚙️ DECISION AUDIT

**Step 1:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null` → **CLEAN** (verified this session)

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| GOVERNANCE_GAP_LOG.md | N/A (not a CANONICAL doc) | GG-012 entry added SESSION 31 | ✅ |
| DECISION_LOG.md | N/A (is the log itself) | T-133 entry + GG-012 entry (commits 1b7ee83, 25dcb7c) | ✅ |
| run_pregame.py | N/A (source file) | GG-012 governance entry covers this change | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260604_1730.md, confirm 715 tests"
# Next action: implement T-134 (TSS size=0 alert in run_paper_trade.py), then wait for G2 resolution at 06:00 UTC Jun 6
```
