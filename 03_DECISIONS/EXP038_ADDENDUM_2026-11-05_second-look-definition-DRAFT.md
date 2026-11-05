# EXP-038 Addendum — second-look definition (2026-11-05)

**Status: PROPOSED — DRAFT. Not frozen. Written by terminal W102.2; only the operator/DS can accept it.** Responds to GG-529.

## The defect
EXP-038 §4: "Second look: judged n = 400 or 2027-01-31, whichever first." It defines neither the games scored nor the n at the date, and §1 ("judged on whatever n they reach") conflicts with §4 ("no scoring before a cell reaches its judged n"). Today the engine releases only n=150 and n=400 and emits no verdict for the date trigger.

## Proposed definition (exact)
1. **Trigger.** The second look fires for a cell on the earlier of: (i) the cell's judged n (settled games with >= 1 scored row, as in §3) reaching 400; (ii) the first daily engine run at or after 2027-02-01T00:00Z, i.e. the day after 2027-01-31 so every game dated <= 2027-01-31 is settled-or-excluded.
2. **Games scored at a date trigger.** All games with game date <= 2027-01-31 that are settled by the trigger run, regular season only (preseason stays excluded, §4). Games unsettled at the trigger are excluded and counted.
3. **n at a date trigger.** Whatever judged n the cell has. If it is below 150 (first-look n), the look is reported as **UNDERPOWERED — no verdict**; the MDE is printed from the realised SD and n. Cells at 150 <= n < 400 are scored under §5 with the wider MDE stated, not tuned.
4. **Once.** The look is taken once, at the first qualifying run, and that run's output is the look. Later runs do not replace it (this resolves the same "which day" ambiguity found in ADR-0072).
5. **§1 vs §4.** §4 governs: no scoring below the cell's judged n, except under item 3's UNDERPOWERED report, which scores nothing.
6. No third look without a new pre-registration (unchanged).

## Open questions for the operator/DS (not answered here)
- Is 2027-02-01 the right settled-day cut, or should the look wait a fixed number of days?
- Should UNDERPOWERED cells (e.g. NBA player points at 0 judged) be allowed to carry past 2027-01-31 under a new pre-registration, or close as UNRESOLVED?
- Should T1/T2/T3 cells sharing a game be looked at on the same run (they are never pooled)?

## Operator decision (one line)
> I accept this second-look definition for EXP-038 as written (earlier of n=400 or the first run on/after 2027-02-01; once; below n=150 reported as underpowered, no verdict).

Calendar second-look state: **draft definition pending operator**.
