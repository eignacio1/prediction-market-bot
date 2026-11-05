# W101.2 Part B: will the engine score NFLQB_NFL_MONEYLINE_T1 on its own? (readiness only; scores suppressed)

Read-only box reads 2026-11-05 (engine output `engine_20261104T135051Z.json`, crontab, ledger, logs). No score, delta or verdict text was read or produced;
the cell is `SEALED (47 of 60)` and the engine writes none below judged n.

| Item | State |
|---|---|
| Trigger | cron `49 13 * * *` UTC `scripts/calibration_engine.py` (W58.3 block); unseals on the first run with judged n >= 60 (QB policy: looks 60 / 150, EXP-037 rule, C2 vs Kalshi mid) |
| Feeders | `14 */6` `run_nfl_qb_challenger_shadow.py --bands T1` and `44 9` settle (`--prefix NFLQB`), both installed, both running (last row 2026-11-04T12:14Z; ledger touched 2026-11-05 00:16Z; settle ran 0 new on the last pass) |
| Rows logged | 528 (engine) in `exp_output/PREGAME_SHADOW_NFLQB/NFLQB_NFL_MONEYLINE_T1.jsonl` |
| Settled games vs judged n | **47 of 60** (78.3%); need 13 |
| Engine projection | **2026-11-13**, schedule method, 151 REG games left x 84% coverage (47 settled of 56 scheduled since 2026-10-11) |
| Data needed by 11-13 | 13 more settled games from: 11-05 (1), 11-08 (13), 11-09 (1), 11-12 (1) = 16 scheduled; the 60th must settle by the 11-13 13:49Z run |
| Blocker | **None.** Nothing to fix by PR. |

**Fragility (not a blocker):** the projection walks cumulative expected games at 84% coverage and crosses 13 at 13.44 on the 11-12 game, so 11-13 holds only if coverage is
about 81% or better on those 16 games (13/16). A below-average week moves the look to the next slate, about 2026-11-16/17 (11-15 adds 12 games, 11-16 one). The look is a
trigger on n, so a slip changes the date, not the procedure.

**Calendar defect found (fixed in Part C, not here):** `PROOF_CALENDAR.md` shows this cell as "season paused / no accrual in the trailing 14d" while the engine shows live accrual. The
calendar's season-window lookup does not know sport `NFLQB` (it is NFL data under another prefix). The 14-day-accrual column for this row is therefore wrong; the engine date is right.

**Pre-registered modal outcome (quoted from `12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md`, EXP-037 first look, same rule the QB cell uses):**
"Vs market, every cell: KEEP ACCRUING ≈ 91%. RULED_OUT ≈ 9% (≈ 16% at n = 150); CANDIDATE < 1%." The QB challenger shares the NFL moneyline frame; the document carries no QB-specific odds.
