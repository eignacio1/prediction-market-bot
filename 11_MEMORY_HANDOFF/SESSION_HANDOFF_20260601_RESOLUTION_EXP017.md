# Session Handoff — 2026-06-01T02:45Z

**Trigger:** Context window limit — operator-initiated handoff
**Last commit:** `dacc2cc` (main) — local only, not pushed to VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 408/408 passing (5 pre-existing scipy/numpy collection errors excluded — test_backtester, test_c3_forecaster, test_exp015_t3_simulation, test_run_backtest, test_scoring_distribution)
- **Capital:** NO live capital — paper trading only (bankroll $1,024.70)
- **VPS:** 157.230.91.33 — cron running; PIPE-03 active nightly
- **Paper bets:** 6/30 resolved (G6 gate) — **see T-110 note below**

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| run_resolve_local.py designated canonical resolution path | stats.nba.com 403-blocks DigitalOcean IPs permanently; VPS resolution always fails. Local SCP pull → resolve → push back is the only working path until VPS IP changes. | DECISION_LOG.md 2026-05-31 | DS |
| summary() redesign: realized_drawdown_pct + deployed_pct | Old drawdown_pct = 31.7% when realized losses = 0% (money in flight miscounted as losses). C4 kill switch was already correct. Explicit split prevents future misreading of capital state. | DECISION_LOG.md 2026-05-31 | DS |
| T2 activation gate corrected: FEATURE_VERSION 1.3.0 removed | EXP-012 falsified the injury signal; v1.3.0 was a placeholder for "after injury features work." Gate now: DS-04 operational + dedicated EXP confirming Brier ≥ 0.001 at N ≥ 100. | EXECUTION_BANDS.md:190; DECISION_LOG.md 2026-05-31 | DS |
| EXP-017 Part A result: edge positive at all market prices 0.40–0.60 | Sensitivity sweep (2,692 TEST rows) shows EV positive at every swept MIP level. EV increases as prices diverge from 0.50. Strong directional evidence for GG-004. Does NOT close GG-004 — actual Kalshi prices required for Part B. | EXP-017_ev-vs-market-price.md; DECISION_LOG.md 2026-06-01 | DS |
| Governance hook bug fixed: grep -v "Status" silently dropped all open governance gap detections | Hook used `grep -v "Status"` to exclude template rows, but GG-004's status line starts `\| Status \| OPEN`. Every session since hook creation has received a false "CLEAN". Fixed to `grep -v "OPEN / IN PROGRESS"`. | .claude/hooks/governance_scan.sh | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Bug I — pd.to_datetime format in resolve_pending() | ✅ COMPLETE — `format="mixed"` added to both Regular Season + Playoffs lookups. Root cause of ALL resolution failures since deployment. |
| Bug J — summary() drawdown metric | ✅ COMPLETE — `drawdown_pct` removed; `realized_drawdown_pct` + `deployed_pct` added. run_paper_trade.py, run_resolve.py, run_resolve_local.py, tests all updated. |
| KI-020 — VPS 403 resolution path | ✅ DOCUMENTED — run_resolve_local.py created. VPS run_resolve.py kept but now logs errors explicitly (was silent). |
| First 6 paper bets resolved | ✅ RESOLVED — 3 Fox WINs + 3 SGA LOSSes. Net P&L: +$103.46. Bankroll: $1,024.70. |
| T-106 — EXECUTION_BANDS.md T2 gate corrected | ✅ COMPLETE — FEATURE_VERSION 1.3.0 removed; gate aligns with BAND_ASSIGNMENT_FRAMEWORK.md. |
| T-105 (partial) — EXP-017 run_exp017.py created; Part A complete | ✅ PARTIAL — Sensitivity sweep run. EV positive at all MIP levels 0.40–0.60. Part B requires operator action (Kalshi price data). |
| Hook bug fix — governance gap false negative | ✅ FIXED — .claude/hooks/governance_scan.sh corrected. GG-004 now correctly surfaced. |
| 4 strategic decisions logged | ✅ COMPLETE — DECISION_LOG.md updated. |

---

## ONE THING PENDING (most critical)

**T-110 — Operator must decide: does 6 = 6/30 or 2/30 toward G6?**

Background: the idempotency bug (pre-T-101) placed 3 identical positions for Fox and 3 for SGA in a single game (SAS vs OKC, May 30). All 6 resolved. They are legitimate paper bets but from a single underlying game event.
- If all 6 count: G6 evidence = 6/30
- If only 2 unique markets count: G6 evidence = 2/30

**Next game:** NYK vs SAS, Jun 3. 3 open positions (from Jun 3 pregame run). After Jun 3, run:
```bash
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
```
This is T-109 (standing procedure).

**GG-004 Part B:** To close the commercial case, collect Kalshi historical prices:
```
GET /trade-api/v2/markets?series_ticker=KXNBAPTS&closed=true
```
Save as `exp_output/EXP-017/kalshi_prices.csv` (cols: player_id, game_date, kalshi_threshold, kalshi_mid_price, kalshi_vig). Then run:
```bash
PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py --kalshi-prices exp_output/EXP-017/kalshi_prices.csv
```

---

## Current Paper Portfolio

- **Bankroll:** $1,024.70 (+$24.70 from initial $1,000)
- **Realized P&L:** +$103.46 (3W / 3L from SAS vs OKC May 30)
- **Realized drawdown:** 0.0% (no permanent losses — SGA losses = $83.76 but Fox wins = +$187.23 gross)
- **Open positions:** 3 (NYK vs SAS Jun 3 — player/threshold TBD from VPS paper_portfolio.json)
- **G6 evidence:** 6/30 resolved (pending T-110 operator decision)

To read live portfolio state:
```bash
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 \
  "cat /opt/prediction-market-bot/logs/paper_portfolio.json" | python3 -m json.tool | head -40
```

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R (run_resolve.py — logs 403 errors, no resolutions; kept for future)
14:00 UTC Mon — Model freshness check
```

**NOTE:** PIPE-03R on VPS will NOT resolve positions (403 block). Resolution requires manual T-109 run.

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016)
3. VPS cannot resolve positions (KI-020 — 403 block). Run `run_resolve_local.py` after each game day.
4. GG-004 is OPEN — commercial case not proven until EXP-017 Part B runs with actual Kalshi prices
5. `dacc2cc` commit is local only — push to GitHub and VPS before or during next session

---

## ⚙️ DECISION AUDIT

Documents modified this session with governance implications:

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| EXECUTION_BANDS.md | N/A (canonical) | T-106 correction logged | ✅ |
| EXP-017_ev-vs-market-price.md | N/A (new) | Part A result logged | ✅ |
| .claude/hooks/governance_scan.sh | N/A (infra) | Bug fix decision logged | ✅ |

Documents with unlogged decisions (pre-existing debt, T-NNN registered):
- EXECUTION_ARCHITECTURE.md (T-093)
- MONITORING_DRIFT_PLAN.md (T-094)
- METHODOLOGY.md (T-095)
- RISK_APPETITE_CONSTRAINTS.md (T-097)
- QUALITATIVE_SIGNALS.md (T-098)
- VENUE_REGISTRY.md (T-096)
- ROADMAP_MILESTONES.md (T-099)

These are LOW priority (T-093–T-099) and deferred to dark period.

---

## ARE WE COMPROMISED? — Session-End Verdict

- **Q1 (Hard limits):** All valid. `max_daily_loss_usd` remains inactive (KI-018 documented). Operative kill switch is 20% drawdown (~$205 at current bankroll).
- **Q2 (Stubs):** 5 known stubs, no new stubs. All assessed.
- **Q3 (Governance gaps):** GG-004 OPEN — EXP-017 Part B pending. **Hook false negative fixed this session.**
- **Q4 (Interfaces):** Single `evaluate_forecast` at risk.py:285. No evolution.
- **Q5 (Traceability):** All hard limits trace to DECISION_LOG. ADR revision at G6 obligated.
- **Q6 (Worried about):** GG-004 commercial case unproven. T-110 ambiguous G6 count. Jun 3 positions pending resolution.

**System is OPERATIONAL with known open items. No blocking issues discovered.**

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260601_RESOLUTION_EXP017.md, confirm 408 tests passing"
```
