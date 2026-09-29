# T-578 — `park_factor_hits` Dead-Feature Audit: Results

**Session/worktree:** `20260929T001608Z-park-factor-dead-feature` · **Task:** T-578 · **Date:** 2026-09-28
**Origin:** item 2 of T-575's ranked feature-audit list (`T575_feature_space_audit_RESULTS.md` §2).
**Tier:** STANDARD — investigated as a suspected live defect, not a feature request.
**ADR:** `03_DECISIONS/ADR-0064_park-factor-hits-venue-name-repair.md` (PROPOSED, not yet accepted).
**Code+tests:** commit `b710609` on `origin/session/20260929T001608Z-park-factor-dead-feature`.

---

## Verdict

**`park_factor_hits` is not dead.** T-575 hypothesized — explicitly flagged as *inferred from
code structure, not live-verified* — that the feature silently defaults to neutral (1.000) on
every row. Direct measurement found this overstated by roughly 6.5x: **15.26%** of all 132,184
historical feature rows (15.30% of the 66,007 home-only rows) are exactly `1.000` due to the
defect; the remaining ~85% carry real, differentiated park-factor values. The defect is a
**venue-name string-matching gap**, not an absent data source — venue data is fetched and present
for the large majority of games; it simply doesn't always match `_PARK_FACTOR_HITS`'s keys
exactly.

## Measured distribution

| Metric | Value |
|---|---|
| Total feature rows | 132,184 |
| Home-only rows (`is_home_game==1`) | 66,007 |
| Rows exactly `1.000` (all rows) | 15.26% |
| Rows exactly `1.000` (home-only) | 15.30% |

Per-team root cause, all confirmed via direct `curl` against the live MLB Stats API schedule
endpoint (several May/June 2026 game dates, this session) — full table in ADR-0064 §2:

- **BAL (100%)** — official venue string `"Oriole Park at Camden Yards"` vs. table key
  `"Camden Yards"`.
- **NYM (100%)** — Citi Field entirely absent from the table.
- **CWS (~62.4%)** — renamed `"Rate Field"`, Feb 2025.
- **HOU (~61.7%)** — renamed `"Daikin Park"`, Jan 2025.
- **ATH (~61.6%)** — home games split across *both* `"Sutter Health Park"` and
  `"Las Vegas Ballpark"` (previously only the former was known/handled).
- **TB (~38.5%)** — 2025 temp relocation to `"Steinbrenner Field"`.
- **LAD (~24.0%, previously unexplained)** — sponsorship-prefixed string
  `"UNIQLO Field at Dodger Stadium"`.
- **AZ, CHC, COL, PHI, STL, CIN, SD, DET (~0.4–1% each)** — unresolved small long tail,
  hypothesized international/exhibition venues. **Not investigated** — honest limitation, not a
  silent gap (see below).

## Cost of the defect (with vs. without re-scoring)

Re-scored the real historical matrix through the unmodified
`scripts/train_mlb_model.py:main()` (`dry_run=True`, no artifacts saved) twice: once with
`park_factor_hits` present in its real, pre-fix degraded state, once with the column dropped.

**Result: near-zero, mixed-direction effect. Both configurations pass the ADR-0009 combined
shadow gate.** Brier delta identical at t=1 (+0.0065), +0.0026 vs +0.0025 at t=2; AUC and ECE
both marginally *worse* with the degraded feature included (by ~0.0004–0.0014). No significance
testing was performed on this delta — it's a point estimate, not a confidence interval. Full
numbers in ADR-0064 §3.

This means the defect was not actively costing the live model meaningfully — but it also means
the feature wasn't helping much in its degraded state, which is exactly why fixing the underlying
match rate (recovering the missing ~15%'s real signal) is worth doing rather than either leaving
it broken or discarding the feature outright.

## Decision: repair, not retire

Implemented (this branch, commit `b710609`): a `_VENUE_NAME_ALIASES` indirection table (BAL,
CWS, HOU, LAD) plus two new `_PARK_FACTOR_HITS` entries (Citi Field, Las Vegas Ballpark), plus an
aggregate `park_factor_venue_unmatched` WARNING audit-log event on every
`compute_features_bulk` call so any future unmatched-venue or missing-venue-data case is now
visible going forward rather than silent. Full rationale in ADR-0064 §4. In short: failures were
mechanical and cheap to fix, the feature already clears the shadow gate even degraded, and
retiring it would discard ~85% real signal to avoid fixing a fixable ~15%.

**Not activated.** The fix exists only on this branch. Per ADR-0042 D2, deploying it to govern
live T1 MLB scoring requires operator sign-off on ADR-0064, a fresh `DEFENSIBLE_IMPROVEMENT`
holdout-gate run, and a production deploy — none of which this session is authorized to perform.

## Prior figures now known to be overstated or affected

- **T-575's own claim** (`T575_feature_space_audit_RESULTS.md` §2): "very likely dead... on
  every row" — corrected to 15.26%/15.30% measured. T-575 flagged this itself as inferred, not
  live-verified; this audit is the live verification.
- **`scripts/t9_gg105_a2_a3_candidate.py`** (`T9_GG105_FEATURE_LEVEL_REWORK_2026-07-28.md`) —
  fit an L2 logistic regression using `park_factor_hits` as one of five `FEATURE_COLS`
  (control, not the variable under test). Result reported: **INCONCLUSIVE**, out-of-fold AUC
  range 0.17–0.78 on n=313. The degraded feature was present as a noisy control in ~15% of
  rows during this fit. Given the result was already INCONCLUSIVE with a very wide AUC range on
  a small n, it is unlikely the park-factor defect drove that outcome — but the run has not been
  re-verified against the repaired feature, so this should be read as *possibly noisier than
  necessary*, not *wrong*.
- **`scripts/g3_gg141_candidate.py`** (`G3_GG141_OPP_SP_BACKFILL_2026-07-29.md`) — same
  `FEATURE_COLS` base (including `park_factor_hits`) extended with backfilled opp_sp columns,
  fit separately for MAIN and T4 via the D1 what-if harness. Same caveat: `park_factor_hits` was
  a control column, degraded in ~15% of rows; result not re-verified against the repaired
  feature.
- **`scripts/t9_gg105_feature_discrimination.py`** — uses `park_factor_hits` in a feature
  mapping for discrimination analysis; not independently re-checked this session beyond
  confirming its presence in the blast radius (grep only).

None of the three scripts above trained or scored a currently-active production model on the
degraded feature in a way that changes a live gate status — all three are research/what-if
artifacts (GG-105, GG-141 tracks), not the live T1 MLB pipeline. Flagged for completeness per
the task's explicit instruction, not because any of them requires re-opening.

## Honest limitations

- Small long tail (~0.4–1% each, 8 teams) remains unresolved — see table above. The new
  aggregate audit-log event will surface these going forward.
- The task asked for a literal historical-row replay of the fix. The stored CSV does not retain
  the raw venue-name string (only the derived float), and no cached raw C1
  schedule/`game_starters` JSON was found locally, so a literal replay wasn't mechanically
  possible. Live MLB Stats API verification was substituted instead — a deviation from the
  literal request, flagged as such rather than silently substituted. See ADR-0064 §6 for full
  discussion.
- No significance testing on the Deliverable 2 with/without delta.

## Gap candidate for 36.3 (GG-145 resolution — NOT registered by this session)

The content below is a proposed correction to GG-145 for session/block 36.3 to register into
`GOVERNANCE_GAP_LOG.md`. This session does not own that file and has not edited it.

> **GG-145 status update candidate:** T-575's hypothesis that `park_factor_hits` defaults to
> neutral on every row is REFUTED IN MAGNITUDE, CONFIRMED IN KIND. Live measurement
> (T-578, 2026-09-28) found 15.26% of 132,184 historical rows affected, not ~100%, root-caused
> per team to a venue-name string-matching gap (missing table entries + unhandled 2025 venue
> renames + one sponsorship-prefixed string), not an absent data source. Fix implemented and
> tested on branch `session/20260929T001608Z-park-factor-dead-feature` (commit `b710609`,
> ADR-0064 PROPOSED) but **not yet activated** — live T1 MLB continues scoring with the degraded
> table pending operator ADR sign-off and an ADR-0042 D2 holdout-gate pass. Recommend GG-145
> move to a status reflecting "root-caused, fix drafted, pending activation gate" rather than
> remaining an open unknown-severity investigation.
