# Session Handoff — 2026-06-03T17:45Z

**Trigger:** Operator-initiated (session end; Finals Game 1 pre-tip preparation complete)
**Last commit:** `dfb16f0` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — T4 running (PID 153790); T1 cron active (21:55/01:25 UTC PIPE-02, 22:00/01:30 UTC PIPE-03)
- **Paper bets:** 0 resolved tonight (Finals Game 1 not yet started) — G6 gate open

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| RESERVE_MANDATE_PCT=0.05 on VPS for Finals G1 paper window | Disconnect 1: at 0.20, floor=$200, max T1 deployable=$800; MC stake=$827 → last 1-2 bets blocked. At 0.05, floor=$50, max=$950 → all 33 bets fire. Paper-window-only; default 0.40 unchanged. | `DECISION_LOG.md` 2026-06-03 SESSION 24 entry | DS |
| pool_isolated=True in PaperTrader.open_position() for T4 | Disconnect 2: after T1 deploys ~$800, bankroll ~$200, T4 `open_position()` returned `(True, {})` on insufficient funds. Empty `pos={}` failed `if pos:` check, silently dropping all T4 bets. Fix: when `pool_isolated=True`, bankroll check/deduction skipped; position still recorded; T4 tracks own pool via `t4_deployed_usd`. | `DECISION_LOG.md` 2026-06-03 SESSION 24 entry; commit `dfb16f0` | DS |
| ~1,000 evaluations = pipeline throughput capacity, NOT bets placed | Clarification of CLAUDE.md Hard Rule 9 design intent. 35 markets × 150 T4 cycles = ~5,250 evaluation calls per game. Bets placed is the edge-gated subset (where p_t4 > mip + vig AND Δp ≥ T4_MIN_DELTA_P=0.08). Architecture is correct; commercial question (how many fire) is calibrated post-G1. | `DECISION_LOG.md` 2026-06-03 SESSION 24 entry | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Push commit dfb16f0 to remote | ✅ `f2a574e..dfb16f0` pushed to `origin/main` |
| VPS git pull — dfb16f0 deployed | ✅ VPS pulled: `paper_trader.py` + `run_t4_live.py` updated |
| RESERVE_MANDATE_PCT=0.05 on VPS | ✅ VPS `.env` updated; `sed -i` confirmed via grep |
| T4 restart with new code | ✅ PID 153790; startup confirmed: flat sizing, pool=$500, PAPER_T4_VIRTUAL=false, game STATUS_SCHEDULED |
| MC re-run confirmation | ✅ 33 bets PLACED, $827 total, no BATCH HALT; advisory reserve warning is display-only |
| Architecture clarification: evaluations vs bets | ✅ Logged in DECISION_LOG; not a code change |
| DECISION_LOG SESSION 24 entries | ✅ 3 entries added |
| TODO_NEXT, MEMORY_BANK, PLAN.md updated | ✅ All last-reviewed dates and milestone notes current |

---

## ONE THING PENDING

**T4 has never fired a live bet.** The game is STATUS_SCHEDULED. At 00:30 UTC Jun 4, ESPN transitions to STATUS_IN_PROGRESS and T4 begins cycling. The key question: do bets actually fire? The pool_isolated fix removes the bankroll-depletion blocker, but the edge conditions (T4_MIN_DELTA_P=0.08, MIN_EDGE=0.02) determine how many evaluations pass. After the game:

1. `ssh root@157.230.91.33 'tail -100 /opt/prediction-market-bot/logs/t4_live.log'` — check T4 FIRED/VIRTUAL lines
2. `ssh root@157.230.91.33 'cat /opt/prediction-market-bot/logs/audit_t4.jsonl | python3 -c "import sys,json; [print(json.loads(l)[\"event\"]) for l in sys.stdin]"'` — event types
3. Run `scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` — calibrate T4_BAND_WEIGHT + T4_EXPECTED_TOTAL_EDGE stubs
4. Run `run_resolve_local.py` to resolve T1 positions

**Next session scope: hygiene and diagnosis only (operator mandate).** No new features. Post-G1 calibration + resolution.

---

## Current Paper Portfolio

- Bankroll: $1,000.00 (reset before Finals G1; 0 open positions currently)
- T1 bets will fire at 22:00 UTC PIPE-03 cron: ~33 bets, ~$827 total stake
- T4 bets will fire during game (00:30–03:30 UTC): unknown count pending first live run
- Closed/Resolved: 0 | G6 gate: 0/66 (APR-0017)

---

## Active Cron on VPS (157.230.91.33)

```
21:55 UTC  — PIPE-02 inference (run_pregame.py) — pregame JSON for MC
22:00 UTC  — PIPE-03 early (paper bets, Finals Game 1 ~20:30 ET start)
01:25 UTC  — PIPE-02 late refresh
01:30 UTC  — PIPE-03 late (backup window)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py) — VPS-side; 403-blocked for stats.nba.com
T4 live:   — run_t4_live.py PID 153790; 60s polling cycle; activates at STATUS_IN_PROGRESS
```

**T4 monitor command:**
```bash
ssh root@157.230.91.33 'tail -f /opt/prediction-market-bot/logs/t4_live.log'
```

**T4 kill switch (if needed):**
```bash
ssh root@157.230.91.33 'touch /opt/prediction-market-bot/logs/t4_kill_switch.flag'
```

**T4 restart command (if process dies):**
```bash
ssh root@157.230.91.33 'cd /opt/prediction-market-bot && nohup bash -c "set -a; source .env; set +a; source venv/bin/activate; PYTHONPATH=src python3 src/prediction_market_bot/run_t4_live.py >> logs/t4_live.log 2>&1" > /dev/null 2>&1 &'
```
**Critical: must include `set -a; source .env; set +a` — omitting causes VENUE_API_KEY not set crash.**

---

## Key Constraints to Remember

1. Next session = hygiene and diagnosis only (operator mandate)
2. No live capital until G6 (APR-0017: EXP-017 Part B confirmed + ≥5 game nights + ≥66 resolved bets)
3. RESERVE_MANDATE_PCT=0.05 is Finals G1 paper window only — do not assume it persists
4. pool_isolated=True is paper-path only; live execution path unchanged
5. T4_BAND_WEIGHT and T4_EXPECTED_TOTAL_EDGE are STUBS — calibrate from tonight's audit_t4.jsonl

---

## ⚙️ DECISION AUDIT

**Step 1 governance scan result:** CLEAN — no `**Decisions logged:** false` documents.

| Document | Decisions logged | DECISION_LOG entries written | Status |
|----------|-----------------|------------------------------|--------|
| `paper_trader.py` (pool_isolated param) | n/a (code) | SESSION 24 entry | ✅ |
| `run_t4_live.py` (pool_isolated call) | n/a (code) | SESSION 24 entry | ✅ |
| VPS `.env` (RESERVE_MANDATE_PCT) | n/a (env) | SESSION 24 entry | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260603_1745Z.md.
# Next session is hygiene and diagnosis only. Begin with session-start protocol."
```

## NEXT SESSION PRIMER

Next session is hygiene and diagnosis only (operator mandate). Start by reading `MEMORY_BANK.md` and `SESSION_HANDOFF_20260603_1745Z.md`, then run the mandatory session-start protocol. The first operational action is post-Finals Game 1 resolution: run `run_resolve_local.py` locally to resolve T1 positions, then check T4 logs via `ssh root@157.230.91.33 'tail -200 /opt/prediction-market-bot/logs/t4_live.log'` to see how many T4 bets fired, then run `scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` to calibrate the two T4 stubs. No new features — hygiene and calibration only.
