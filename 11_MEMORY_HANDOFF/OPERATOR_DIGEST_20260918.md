# Operator Digest — 2026-09-18

## T-559/GG-291 — NFL's first real settlement would have crashed. Caught it in rehearsal, not on game day.

I rehearsed settlement on a disposable copy with made-up scores before touching the real 42 NFL bets. It crashed: all 42 are missing a data field settlement needs for win/loss — a gap from how they were opened. It would have failed hard on the real run, likely 2026-09-21.

Didn't touch real bets or fix live (out of scope). Registered GG-291 (high severity); confirmed the rest of settlement logic is correct via a rehearsal patch (16/18 matched hand-calc; a tied game was correctly refused, not guessed); wrote a runbook making the fix the mandatory first step for 2026-09-21.

**Next:** fix GG-291 before real settlement — `04_EXECUTION/NFL_T1_FIRST_SETTLEMENT_RUNBOOK.md`. No real bets touched, no fake scores near the real ledger.
