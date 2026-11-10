# W107.3 (B-061) threshold, written BEFORE any outcome was read

Written 2026-11-10 ~02:30Z, before loading any settlement/outcome field. Only v2/v3 `p_engine` values and Kalshi quotes had been inspected for structure.

- **Availability-moved game** = a ticker where |p_v3 - p_v2| >= 0.03 (3 points of probability; chosen because it exceeds the 1.5-2.3c taker cost per side on game lines, 106.2). Game-level flag: any ticker of the game meeting it.
- **Moved toward v3 later** = Kalshi mid, measured from v3's `quote_ts` to tip-minus-10-minutes, changes by >= 1c in the direction of (p_v3 - p_market). "Same time" / "not" = within +-1c / the opposite direction.
- Scores are DESCRIPTIVE. EXP-044c's frozen looks are untouched. No verdict below judged n.
