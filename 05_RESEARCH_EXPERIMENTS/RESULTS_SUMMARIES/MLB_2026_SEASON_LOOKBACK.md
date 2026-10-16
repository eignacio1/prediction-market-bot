# MLB 2026 season look-back (W80P.4, written 2026-10-16, before the World Series ends)

**Purpose (Hard Rule 12):** PROOF — P1 (MLB cells at a scored look / MLB logging cells), P2 (verdicts issued), P3 (next look).
**Written from a cloud session with no box access** (no `ssh` binary; Kalshi and the dashboard refused by the session's
network policy). Every count below is quoted from a dated repo source; none was re-read from a ledger today. The final
read is `scripts/mlb_season_lookback.py`, run once on the box after the last World Series game settles (§4).

## 1. Cell-by-cell

| MLB cell (MARKET_TYPE_REGISTRY) | Status | Governing rule | Judged n / look | Reached? | Verdict |
|---|---|---|---|---|---|
| Moneyline × T1/T2/T3 | SHADOW (postseason rows) | EXP-037 MLB pre-registration (2026-10-02) | 150 settled **2027 regular-season** games per cell, then 600. §0: "every row banked from [the 2026 postseason] … are NEVER scored at any look, and may only be counted." | **No — not reachable from 2026 by design** | none; none possible |
| Run line × T1/T2/T3 | SHADOW (postseason rows) | EXP-037 MLB | same | No (by design) | none |
| Game total × T1/T2/T3 | SHADOW (postseason rows) | EXP-037 MLB | same | No (by design) | none |
| Team total × T1/T2/T3 | SHADOW (postseason rows) | EXP-037 MLB | same | No (by design) | none |
| Player hits × T1 / T2 / T3 | SHADOW (paper book; `kelly_fraction` 0, ADR-0048) | APR-0024: clean_n ≥ variance-derived n* per band (GG-004) | T1 last recorded **clean_n 81 / n\* 2,322** (GG-004, read 2026-07-15) | No (last read; not re-derived since — GG-004 "Not re-derived this session", 2026-10-08) | none. Offline model EXP-028: skill over climatology detected (ΔBrier +0.0052 [0.0044, 0.0060]), **edge over market NOT TESTABLE** (0 priced rows), P5 control failed its literal criterion |
| Player hits × T4M-PROJ | ACTIVE (flat demo stakes, ADR-0050) | APR-0024 n* on **CONFIRMED_FILLED** rows only (GG-527) + G6 | last recorded clean_n 338 / n\* 787 (2026-07-15, **pre-GG-527**: counted paper rows, so not comparable) | Not established on fills | none. T-569 latency thesis: **NOT SUPPORTED (current feature set)**; T-572 CLV: INCONCLUSIVE |
| Player hits × T4M-ARITH / T4M-FLOW | BLOCKED | — | — | n/a (no rows) | none |
| Partial game, T4 in-play, T5 (all families) | NOT_IMPLEMENTED | — | — | n/a | none |

**Execution (fills only, GG-527)** — last generated values (`scripts/distance_to_optimum.py`, VPS run 2026-10-09 + 63.3,
RUNNING SITREP): **E1** T4 MLB 166 / 4,237 = 3.9% filled; T1 MLB 85 / 485 = 17.5%. **E2** P&L per filled bet T4 −$0.26
(95% CI −0.45..−0.07), T1 −$1.50 (CI −3.67..+0.63). **E3** win rate fills vs non-fills T4 24.1% vs 48.7%, T1 28.9% vs 52.1% —
adverse selection on fills. The T4 E2 interval excludes zero on the negative side; that is an execution reading, not a
pre-registered verdict (T4M-PROJ's rule is n* on fills, §1).

## 2. What the season proved (rigorous, from the above)

1. **No MLB cell reached a scored look in 2026. P1 = 0 / 16 MLB logging cells; P2 = 0.** For the 12 game-market cells this
   was fixed in advance (EXP-037 §0) — it is the pre-registration working, not a shortfall.
2. **Pre-game player-hits skill over climatology is real but small and largely persistent skill/role a market prices**
   (EXP-028 P1/P4). Edge over the market was never testable on the pre-game substrate.
3. **T4M-PROJ's licensing thesis failed its own test** (T-569 NOT SUPPORTED) and its fills show adverse selection
   (E3) with negative P&L per filled bet (E2). No verdict under its pre-registered n* rule has been read on fills.
4. **What was not proven:** edge in any MLB cell. The commercial question (GG-004) stays OPEN into 2027.

## 3. Next look (P3)

MLB: **2027 regular season**, EXP-037 first look at 150 settled games per cell (earliest-150 by `(start_time_utc,
game_key)`, write-once manifest). The modal first-look outcome pre-registered there is SHADOW (CI spans zero; MDE ≈ 0.011 vs
a plausible true effect ≤ 0.01). T4M-PROJ stops after the 2026 World Series (EXECUTION_BANDS.md, GG-527).

## 4. Final read — command and date

Run **once, the day after the final 2026 World Series game settles** (check the MLB Stats API schedule for the last
game date; settlement is Kalshi's, ADR-0071), on the box:

```bash
cd /opt/prediction-market-bot && PYTHONPATH=src venv/bin/python scripts/mlb_season_lookback.py \
    --out 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/MLB_2026_SEASON_LOOKBACK_FINAL.md
```

It reads the calibration engine (EXP-037 seal status per MLB cell), `run_power_calc.run_all_bands` (APR-0024 n*, T4M-PROJ
on CONFIRMED_FILLED only) and `distance_to_optimum.execution` (E1–E3). It computes no new score; any unreadable source
prints UNAVAILABLE. It is not a running component. Commit its output docs-only and replace the dated figures in §1.
