# Next Session Handoff Prompt

**Paste this entire block into the next terminal window to resume.**

---

You are resuming work on the Prediction Market Trading Bot (Compass OS governance framework). This is a solo-operator paper trading system targeting NBA player prop markets on Kalshi/Polymarket. Read the following before doing anything else.

## Step 1 — Read these files immediately (in order)

1. `11_MEMORY_HANDOFF/MEMORY_BANK.md` — 10 anti-context-erosion invariants; these are LAWS
2. `11_MEMORY_HANDOFF/SESSION_HANDOFF_20260602_1400.md` — SESSION 15 state (ADR-0012 / KI-018 resolved)

Do NOT proceed past Step 1 until both are read.

## Step 2 — Governance scan

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null
```

Expected result: CLEAN (all 7 prior files flipped to `true` in SESSION 15 — T-093–T-099).

## Step 3 — Confirm build integrity

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
python3 -m pytest tests/ -q
```

Expected: **695 passed**.

## Step 4 — Check paper portfolio on VPS

```bash
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 "python3 -c \"import json; d=json.load(open('/opt/prediction-market-bot/logs/paper_portfolio.json')); print('Bankroll:', d.get('bankroll_usd')); print('Open:', len(d.get('open_positions',[]))); print('Closed:', len(d.get('closed_positions',[])))\" "
```

Expected pre-G1: `Bankroll: 1000.0 | Open: 0 | Closed: 0` (clean slate; T1 pre-game bets for G1 (Jun 3) placed by Jun 2 22:00 UTC cron).

After G1 resolves, run `T-109 resolve procedure` locally (VPS 403-blocks nba_api):
```bash
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
```

## Step 5 — First task

Read `04_EXECUTION/TODO_NEXT.md` → highest priority executable task.

---

## Key invariants (do not lose these)

1. **arb/ folder = REFERENCE ONLY** — gate is APR-0010 (not signed). No arb code active.
2. **No real capital until G6** (ADR-0005 + DS sign-off). Paper trading only.
3. **ADRs are immutable.** Superseding ADR required for any change.
4. **G6 threshold = ≥66 resolved paper bets + ≥5 game nights** (APR-0017 — supersedes APR-0016). Binding constraint is GG-004 (EXP-017 Part B CONFIRMED) + 5 nights for slope df.
5. **FEATURE_VERSION = 1.2.0** — NOT 1.3.0. v1.3.0 was built but HYP-006 FALSIFIED it (EXP-012). F-039/F-040 dropped.
6. **T1 is ACTIVE. T2/T3 are SKELETON. T4/T5 are paper-scope prototype (ADR-0011) — NOT live orders without Phase 8 ACTIVE gate (EXP-018/019).**
7. **Kelly fractions (ADR-0010):** T3=0.07 < T1=0.10 < T2=0.13 < T4=0.20 < T5=0.25.
8. **Daily loss kill switch = 15% of initial_bankroll** (ADR-0012; $150 at $1,000 paper). Recalibrate at G6.
9. **Kill switch ≤60s** (NFR-03). Hard limits: $500/bet, 20% drawdown trigger.
10. **No task block starts without `/checkpoint` for the block just completed** (MEMORY_BANK invariant #10).
11. **T-129 Path B (Poisson CDF per threshold) is LIVE** — GG-008 RESOLVED. run_paper_trade.py uses `p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, pts_mean)`. Old LR p_est = phantom edge at extremes.
12. **Health check has two false-negative FAILs** (Python 3.11 check vs 3.12 venv; Kalshi API ping broken). Cron runs correctly despite these. Fix before G6.

---

## Current system state (as of 2026-06-02 SESSION 15)

| Field | Value |
|-------|-------|
| Phase | 6/7 ACTIVE |
| VPS | 157.230.91.33 — cron running |
| Tests | 695/695 passing |
| Paper bets | 0 resolved / 0 open — clean slate; G6 gate: 0/66 (APR-0017) |
| Bankroll | $1,000.00 (reset 2026-06-02 after GG-008 wipe; 0% drawdown) |
| Experiments | 16/16 complete; EXP-017 Part B LIVE (n=2, DIRECTIONAL_POSITIVE; GG-004 OPEN) |
| Hypotheses | 9/9 resolved |
| Capital | NO live capital — paper only |
| Model | v1-28483b21; Brier 0.2461; EV +$0.0958/bet (vs null; GG-004 is the real question) |
| FEATURE_VERSION | 1.2.0 (78 features: 31 quant + 47 qual) |
| NBA Finals | NYK vs SAS — **G1 Jun 3** (game time ~22:00 UTC) |
| Next milestone | G1 resolves → run T-109 locally → first clean G6 evidence bets |

**VPS cron schedule:**
```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

**Connectivity:** Any non-work network passes Kalshi WAF. Work wifi blocks outbound.

---

## What was completed recently

**SESSION 15 (2026-06-02):**
- KI-018 RESOLVED — `MAX_DAILY_LOSS_PCT=0.15` replaces zombie `max_daily_loss_usd=1000.0` (ADR-0012)
- `initial_bankroll` parameter added to `RiskEngine` — two independent kill switches restored
- RESERVE_MANDATE_PCT=0.40 advisory wire in `evaluate_forecast()`
- Documentation debt T-093–T-099 CLEARED (7 files, 8 DECISION_LOG entries)
- 695/695 tests; commit 9337d14; VPS current

**SESSION 14 (2026-06-02):**
- T-129 Path B — Poisson CDF per threshold (GG-008 RESOLVED)
- ADR-0010 ACCEPTED — Band Kelly hierarchy (T3=0.07 < T1=0.10 < T2=0.13 < T4=0.20 < T5=0.25)
- ADR-0011 ACCEPTED — Phase 8 T4/T5 paper prototype scope
- DS-02 adapter (`ds02_nba_live.py`), `reset_paper_portfolio.py` built
- Portfolio wiped + reset to $1,000 clean slate
- 692/692 tests; commits d8340ba + 1d10b7e; VPS current
