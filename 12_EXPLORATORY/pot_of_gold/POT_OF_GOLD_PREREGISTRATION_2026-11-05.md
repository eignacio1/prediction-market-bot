# Pot-of-gold pre-registration (committed 2026-11-05, before any forward row)

**Cells:** the 17 cells in `src/prediction_market_bot/decision_trees/longshot_cells.toml` (route x family x bucket x time-to-start; book "all"), all status IN_SAMPLE.
No other cell may be promoted from this wave's data.
**Forward data:** quotes archived after 2026-11-05, first two-sided pre-start snapshot per (ticker, tier), same method as `measure.py`. Paper only.
**Judged n:** 150 forward contracts across at least 30 games AND at least 5 outcomes of the rarer kind, per cell.
**Looks:** 2026-12-10 and 2027-01-14 (scored only for cells at judged n). No score is read below judged n.
**Decision words:** PASS = forward net lower bound (game-clustered, 90%) above 0, Holm-adjusted across the cells at that look -> status FORWARD_PASSED.
FAIL = forward net mean at or below 0 at judged n -> FAILED. Otherwise CONTINUE.
**Modal outcome (stated in advance):** most cells FAIL or stay CONTINUE; 0-2 PASS. Pooled gaps are about 1c against costs of 1-3c, so a pass is the exception.
**Conflicts:** no cell is a frozen test or an EXP-042/043 arm by name; I did not re-read those pre-registrations this session, so the strategic window should confirm.
**Guardrails:** no real capital, kelly_fraction 0, no orders this wave.
