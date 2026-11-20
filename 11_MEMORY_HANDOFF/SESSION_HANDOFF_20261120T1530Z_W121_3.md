---
block: W121.3 (B-097) capacity and dollar ceiling
vision_pillar: EXECUTION
gap_measure: E-pillar fillable contracts per cell (median); $/day ceiling per arm per sport at $1k/$10k/$100k; top 10 cells
gap_delta: from none measured to 51 cells with live cross-touch depth (NBA 24, NHL 18, NFL 9 with n=0 depth); ceilings stated for 6 arm x sport pairs
pattern_sweep: box result 60 KB cap truncated indented JSON -> capacity_read now compact; other box reads (arm_orders_read, d6_read) can hit the same cap, not swept here
surface_delta: 0 new live components; 1 read-only allowlisted box task (capacity_read)
directive_conflicts: none (grep of OPERATOR_DIRECTIVES.md for capacity/ceiling/sizing/kelly found only the wave header)
---
# W121.3 handoff
**Result:** `12_EXPLORATORY/capacity/RESULT.md` (+ `capacity_table.csv/json`, `ceiling.json`, raw `capacity_read_20261120.json`). PRs #536, #539. First line of COMMON_RULES_W121.md was quoted at session start.

## MEASURE MOVED
- Median cross-touch contracts per cell: see table; by arm x sport medians of cell medians: FADE NBA 244, MOMENTUM NBA 503, RIDE NBA 1,044, FADE NHL 16,787, MOMENTUM NHL 6,110, RIDE NHL 2,637 (NHL large = quotes away from touch, not capacity).
- $/day ceiling at $1k / $10k / $100k (point [low, high]): FADE NBA 1,116 / 1,107 / 1,107 [-106, 2,348]; FADE NHL 63 / 64 / 64; MOMENTUM NBA 86; MOMENTUM NHL 7; RIDE NBA 10; RIDE NHL 7. $10k = $100k because the $25 event cap binds.
- Top 10 (by $10k ceiling): NBA spread T3 FADE 831; NBA spread T2 FADE 138; NBA game total T2 FADE 101; NHL game total T2 FADE 51; NBA spread T2 MOMENTUM 33; NBA game total T3 FADE 29; NBA team total T2/T3 MOMENTUM 18 / 14; NBA game total T2 MOMENTUM 9; NBA team total T2 FADE 9.

## Honest limits
- **Ticks 1/2/3 not measurable:** orders log touch only; ladder archive had 0 files on the box; no NBA/NHL ladder exists. NFL arm orders log no depth (n=0, no ceiling).
- Every net interval spans 0, so every ceiling's low is negative. Net is pooled per arm (W117.1). MODEL_FADE has no estimate.
- Windows are 4-9 days. 33 of 51 cells have n < 30.
- Ranking is NOT a sizing rule. Kelly 0, no capital moved.

## For the window
1. Decide whether to add NBA/NHL ladder capture (new live component, install gate).
2. Why DEPTH_ARCHIVE is empty on the box and why NFL arm orders carry no book_at_submit.
3. Per-cell net estimates when n allows.
