# Thin-market pre-registration — NFL player passing yards (KXNFLPASSYDS), pre-game

**Status: FROZEN 2026-10-20 (W80.1). ACCEPTED by the operator 2026-10-19 21:40 PT (strategic window, AskUserQuestion: "Yes, accept it (Recommended)"); authorization is the blockquote in `04_EXECUTION/ACTIVE_QUEUE.md` "Needs your decision". Logging against it may begin (SHADOW, no orders, kelly 0).** Status line only changed; the text below is untouched. Any change after freezing is a new dated file.
Pillars: BREADTH + EXECUTION. Operator thesis carried: "beating buddy off his phone placing parlays, that's the first step"; 77.2b: thinner-edge pre-registration before any new NFL game-market factor.

## 1. Family and cells
Series `KXNFLPASSYDS` (one strike ladder per starting QB per game), pre-game band T1 only, SHADOW (evaluate and log; no orders). Follow-on families, each needing its own pre-registration: `KXNFLRECYDS`, `KXNFLRSHYDS`.
Why this family first (from `results.md`, 2025-and-earlier): ≥47 events so intervals are usable; spread 5.0¢ [5.0, 6.0]; 71% of in-game snapshots show ≥10 contracts within 2¢ of mid (n=238), the best of the three yardage props; thin (fillable-hour share 0.15 [0.09, 0.22]) so retail-driven, with game ML (0.96) as the efficient contrast.

## 2. Factor
Starting-QB availability and QB-vs-defense matchup (F8 availability class plus pass-defense matchup), converted to a probability for each passing-yards strike. Stage on freeze: availability aggregated; matchup interpreted; none applied.

## 3. Expected edge, stated before looking
**Thinner edge expected.** Expected gross edge 1–2¢ per contract. The half-spread alone is ~2.5¢, so the **modal outcome is no fill-adjusted edge** (P ≈ 0.7). A positive verdict needs the model to beat the book mid by more than the half-spread on fillable quotes.

## 4. Judged n and test
Unit: a priced strike with a fillable quote at the pre-kickoff snapshot. Judged n = **400 such strikes across ≥ 60 distinct games** (clustered by game). Score: paired Brier difference (model minus mid), one-sided 95% cluster bootstrap CI; separately, net P&L per contract after crossing the spread. At paired-diff sd ≈ 0.25, n=400 gives SE ≈ 0.0125, so ≈ 0.02 Brier is detectable. No score read below judged n. Verdict set: SUPPORTED / NOT SUPPORTED / UNDERPOWERED.

## 5. Fillability floor (from Part A depth)
A strike counts only if, at the snapshot, the cheaper side shows **≥ 10 contracts within 2¢ of mid** and spread ≤ 6¢. Rationale: flat demo stake ≈ $1 (≈ 2 contracts at mid 0.5), and 10 contracts keeps the stake under ~20% of top depth. Caveat: this floor rests on **in-game** depth (n=238). Pre-kickoff NFL depth is n=0 today; the floor is re-checked against the first full NFL week of forward capture and, if pre-kickoff P(≥10 @2¢) is under 40%, the family is marked UNDERPOWERED-BY-LIQUIDITY rather than rescored.

## 6. What the capture must record (per snapshot)
`ticker`, `event_time`, `secs_to_kickoff_est`, best bid/ask, contracts within 1/2/5¢ of mid per side, spread, model_p, the factor inputs and their as-of times (QB status, injury designation, opposing defense features), and whether the quote met the floor. Cadence: hourly exists; a **30-minute pre-kickoff** snapshot is required for the 2h/30min questions and needs a new cron line (new-shadow-line authorization applies; not built here).

## 7. Out of scope / guardrails
No order, no stake, `kelly_fraction` 0, no real capital. 2026-season rows are scored only at the judged n.

**Operator ask (one line):** Accept KXNFLPASSYDS (T1, shadow) as the first thin-market cell on this pre-registration? Recommend: yes, with the 30-minute snapshot line built this week.
