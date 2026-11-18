# Session Handoff — 2026-06-09T17:00Z

**Trigger:** Operator-initiated session end
**Last commit:** `ba1a92a` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 783/783 passing (no code changes this session block)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; ba1a92a deployed at /opt/prediction-market-bot
- **Paper bets:** 82 resolved (66 unique T1 markets, at APR-0017 floor) — T4: 1,115 resolved

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GG-004 / Hypothesis C: pending DS decision | EXP-018 shows EV=-$0.0014/bet overall (CONFIRMED_NEGATIVE) but +$0.0202 injury-filtered. Hypothesis C technically triggered (EV ≤ 0 at n=66). Three views offered; recommendation is View C (wait for G4 data). Not formally decided. | DECISION_LOG.md 2026-06-09 [SESSION 41 cont.#2 / EXP-018] | DS |
| EXP-018 mip methodology question: pending | EXP-017 Part B uses pregame mid_price (+$0.0050); EXP-018 uses entry price (-$0.0014). For commercial validation, entry price is the correct measurement. Which governs EV claims? Not decided. | DECISION_LOG.md same entry | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| `scripts/run_exp018.py` | ✅ Built, syntax-checked, run on G2+G3 data. adj_λ EV test. |
| EXP-018 result | ✅ n=66, overall EV=-$0.0014 (CONFIRMED_NEGATIVE), injury-filtered +$0.0202 (DIRECTIONAL_POSITIVE). YES bets +$0.0733 (n=24), NO bets -$0.0440 (n=42). opp_adj_factor=0.9586 < 1.0 (direction correct). |
| `scripts/post_game_g4_resolve.sh` | ✅ Built (10 steps): T1+T4 resolve, SCP 5 files from VPS (T1 portfolio, T4 portfolio, pregame_20260610.json, spread_observations.jsonl, t4_position_trajectories.jsonl), VPS git pull, EXP-017 Part B rerun, EXP-018. |
| Mac crontab | ✅ Scheduled: `0 23 10 6 *` (11 PM PDT Jun 10). G3 cron entry replaced. |
| GG-004 analysis | ✅ Three views (Hypothesis C / injury contamination / wait for G4) surfaced and explained to DS. No formal decision made. |
| DECISION_LOG.md | ✅ Entry added: EXP-018 result + two pending DS decisions. |
| MEMORY_BANK.md, TODO_NEXT.md, PLAN.md | ✅ All updated with EXP-018 results and G4 workflow status. |
| VPS deploy | ✅ Commit ba1a92a: run_exp018.py + post_game_g4_resolve.sh + exp_output/EXP-018/ + docs. |

---

## ONE THING PENDING

**DS decision on GG-004 trajectory.** EXP-018 produced CONFIRMED_NEGATIVE overall (EV=-$0.0014/bet, n=66 — at the APR-0017 statistical floor). EXP-018 spec says Hypothesis C is triggered. But injury-filtered is positive (+$0.0202). The decision determines whether G6 requires a model revision pass before live capital, or whether G4+G5 data resolves it.

State as of session end:
- G4 post-game script is READY and SCHEDULED (11 PM PDT Jun 10 automatic)
- After G4 resolves, EXP-018 will auto-rerun with n~100-115 unique markets
- If injury-filtered EV stays positive at n~100+, the case for View B (contamination explains it) strengthens considerably
- DECISION_LOG entry written: two explicit questions for DS

Next action: **Wait for G4 auto-resolve (Jun 10 11 PM PDT), then read updated EXP-018 results at `exp_output/EXP-018/EXP-018_results.json`. Then make the GG-004 call.**

---

## Current Paper Portfolio

- **T1 bankroll:** $876.83 (12.3% realized drawdown from $1,000)
- **T4 pool:** $1,539.42 (from $500 initial)
- **Open:** 0 (between games)
- **T1 resolved:** 82 positions (66 unique markets, 64.6% win rate, cumulative P&L=-$123.17)
- **T4 resolved:** 1,115 positions (51.4% win rate, P&L=+$39.44)
- **G6 unique market floor:** 66/66 ✓ — bet count floor met; game-night floor 2/5 not yet met

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check (PIPE-01)
21:30 UTC  — PIPE-02 inference (run_pregame.py) — writes pregame_YYYYMMDD.json
22:00 UTC  — PIPE-03 early paper bets (run_paper_trade.py, 7pm ET games)
01:30 UTC  — PIPE-03 late (9pm+ ET games)
06:00 UTC  — PIPE-03R resolve (run_resolve.py)
23:00 UTC  — PIPE-07 T4 live (run_t4_live.py) — spread+trajectory logging active from G4
```

```
MAC (Jun 10 only):
0 23 10 6 * — post_game_g4_resolve.sh (11 PM PDT Jun 10)
```

---

## Key Constraints to Remember

1. **GG-004 OPEN + Hypothesis C technically triggered** — EXP-018 EV=-$0.0014 at n=66. DS decision required before calling G6. G4 data will clarify.
2. **Drawdown proximity:** Bankroll $876.83, 12.3% realized drawdown. 15% kill switch fires at ~$144 total realized loss. ~$7.83 additional headroom at current bankroll. A bad G4 night could cross it.
3. **GG-018 OPEN:** APR-0017 66-bet floor was derived T1-only. T4 at 1,115 bets/game invalidates evidence pooling premise. T-148 registered — ADR required before G6 called.
4. No live capital until G6 (APR-0017: ≥66 unique resolved bets + ≥5 game nights + GG-004 CONFIRMED POSITIVE + DS sign-off).
5. arb/ folder = REFERENCE ONLY (APR-0010 required before activation).

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents found.

| Document | decisions_logged | DECISION_LOG entries | Status |
|----------|-----------------|----------------------|--------|
| scripts/run_exp018.py | N/A (script) | EXP-018 finding logged | ✅ |
| scripts/post_game_g4_resolve.sh | N/A (script) | Implementation only | ✅ |
| exp_output/EXP-018/EXP-018_results.json | N/A (data) | Finding logged in DECISION_LOG | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260609_1700.md.
#   G4 was Jun 10. post_game_g4_resolve.sh ran automatically at 11 PM PDT.
#   Key pending: DS decision on GG-004 (Hypothesis C vs View C).
#   Check exp_output/EXP-018/EXP-018_results.json for updated n."
```
