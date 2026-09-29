# ADR-0064 — Repair `park_factor_hits` Venue-Name Matching (Draft, Not Activated)

**Status:** PROPOSED — drafted 2026-09-28 (session/worktree
`20260929T001608Z-park-factor-dead-feature`, T-578) as item 2 of T-575's ranked feature-audit
list. Not yet ACCEPTED — operator signature required. This document changes `_PARK_FACTOR_HITS`
and `_VENUE_NAME_ALIASES` in `mlb_features.py` (already landed to this branch, commit `b710609`)
but does **not** activate that change against the live pipeline: no model retrain, no
`models/` artifact save, no VPS deploy, no `kelly_fraction`/cell-status/gating-constant change.
All re-scoring performed under this investigation used `dry_run=True`.

**Depends on / builds on:** T-575 (feature-space audit that originated the "likely dead" hypothesis
this ADR corrects and resolves — see §1). GG-145 (OPEN gap this ADR's evidence should inform when
"36.3" registers the corrected resolution — this session does not edit `GOVERNANCE_GAP_LOG.md`
itself, see Scope). ADR-0009 (shadow-gate criteria used to evaluate the with/without re-scoring
delta, §3). ADR-0042 D2 (`DEFENSIBLE_IMPROVEMENT` holdout gate — the gate this fix must clear
before activation, §5). ADR-0004 (frozen-model policy — this ADR does not retrain or activate a
model; it repairs an already-computed input feature's derivation).

**Registers:** No new `GG-NNN` opened directly by this session (T-578 does not own
`GOVERNANCE_GAP_LOG.md`). Gap-candidate content for "36.3" to register — refuting the ~100%
magnitude T-575/GG-145 hypothesized while confirming and precisely root-causing the real ~15.26%
defect — is recorded in
`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T578_park_factor_hits_audit.md` §"Gap candidate for
36.3", not here.

**Author:** Session/worktree `20260929T001608Z-park-factor-dead-feature` (T-578)

**Scope:** `mlb_features.py`'s park-factor derivation path, its feature contract, the T1 MLB
consumer, tests, this ADR draft, and the linked results summary. Does **not** touch
`run_t4_mlb_live.py`/`MLBLiveBatterState` (owned by session/block 36.2), does **not** edit
`GOVERNANCE_GAP_LOG.md`/`DECISION_LOG.md` (owned by 36.3), does **not** change any
`kelly_fraction`/cell status/gating constant, does **not** repair or re-stamp any ledger row
(cohort T-577 is UNRECOVERABLE and out of scope), and does **not** restart any production service.

---

## 0. Central claim

`park_factor_hits` is not dead. T-575 hypothesized (explicitly flagged as *inferred from code
structure, not live-verified*) that the feature silently defaults to neutral on **every** row,
because the C1 venue-name fetch appeared to have been disabled after a CDN 406 error. Direct
measurement of the historical feature matrix (132,184 rows) found this hypothesis wrong in
magnitude: **15.26% of rows** (15.30% of the 66,007 home-only rows) are silently neutral, not
~100%. Venue data is fetched and present for the large majority of rows; the defect is a
**venue-name string-matching gap** in `_PARK_FACTOR_HITS`, not an absent data source. Root-caused
per team via live MLB Stats API verification (§2). The fix — a `_VENUE_NAME_ALIASES` indirection
table plus two previously-missing entries — is mechanical, cheap, and does not require retiring
the feature: the pre-fix degraded feature already clears the ADR-0009 shadow gate with near-zero
net effect (§3), so repairing it recovers real signal on ~15% of rows at no measured downside.

---

## 1. What T-575 got right and wrong

T-575 (`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T575_feature_space_audit_RESULTS.md` §2) stated:

> `park_factor_hits` is very likely dead in production (inferred from code structure, not
> live-verified). It's keyed by venue name, but the C1 fetch that would supply venue name was
> disabled after a CDN 406 error, and the inline comment claiming a team-abbreviation fallback
> exists is not supported by any code path found. If true, T1 MLB has been training and scoring
> on a park-factor feature that silently defaults to neutral (1.000) on every row.

**Right:** the inline comment claiming a team-abbreviation fallback was indeed unsupported by any
code path — it was simply wrong, and has now been corrected (`mlb_ingestion.py`, this branch).
`park_factor_hits` is genuinely keyed on venue name, and the CDN 406 issue on the `venue` hydrate
parameter is real.

**Wrong:** the 406 only affects the *hydrated* `venue` parameter. The **base, non-hydrated**
schedule response still includes `game.venue.{id,name}` for the large majority of games — this
is what `park_factor_hits` actually consumes (via `game_starters`, populated in C1). Venue data is
not systematically absent; it is present and mostly matches. The defect T-575 correctly sensed
(a real gap between documentation and implementation) was real, but its severity was overstated
by roughly 6.5x (100% hypothesized vs. 15.26% measured) because the hypothesis was never checked
against the actual data.

---

## 2. Measured defect and root cause, by team

Measured against `exp_output/MLB/mlb_feature_matrix.csv` (132,184 rows; 66,007 `is_home_game==1`
rows used for the per-team breakdown, since `park_factor_hits` is a home-venue-keyed feature).
Overall: **15.26%** of all rows, **15.30%** of home rows, exactly `1.000`.

Root cause confirmed per team via direct `curl` calls to the live MLB Stats API schedule endpoint
(`https://statsapi.mlb.com/api/v1/schedule`, several May/June 2026 game dates, this session):

| Team | Miss rate (home rows) | Root cause | Fix |
|---|---|---|---|
| BAL | 100% | Official venue string is `"Oriole Park at Camden Yards"`, table key was `"Camden Yards"` | Alias |
| NYM | 100% | Citi Field entirely absent from the table | Added entry (0.960, Baseball-Reference multi-year batting PF) |
| CWS | ~62.4% | Renamed `"Rate Field"` Feb 2025 | Alias to `"Guaranteed Rate Field"` |
| HOU | ~61.7% | Renamed `"Daikin Park"` Jan 2025 | Alias to `"Minute Maid Park"` |
| ATH | ~61.6% | Splits home games across **both** `"Sutter Health Park"` and `"Las Vegas Ballpark"` (confirmed live — previously only Sutter Health Park was known) | Both entries, explicit documented neutral (1.000; no established multi-year MLB PF for either Triple-A facility) |
| TB | ~38.5% | 2025 temp relocation to `"Steinbrenner Field"` (Tropicana Field storm damage); confirmed back at `"Tropicana Field"` live by June 2026 | Explicit documented neutral for the temp venue; historical miss concentrated in 2025-dated rows |
| LAD | ~24.0% (previously unexplained) | Venue string carries a sponsorship prefix, `"UNIQLO Field at Dodger Stadium"` | Alias to `"Dodger Stadium"` |
| AZ, CHC, COL, PHI, STL, CIN, SD, DET | ~0.4–1% each | Unconfirmed — small long tail, hypothesized international/exhibition-game venues | Not investigated; flagged as an honest limitation (§6) |

---

## 3. Cost of the defect (Deliverable 2, re-scoring delta)

Re-scored the existing historical feature matrix twice through the unmodified
`scripts/train_mlb_model.py:main()` entrypoint (`dry_run=True`, no artifacts saved): once with
`park_factor_hits` present (real, pre-fix degraded values), once with the column dropped
entirely. This isolates the **pre-fix** feature's net contribution — it does not and cannot
measure the fix's benefit directly, since the historical CSV stores only the derived float, not
the raw venue string needed to replay the fix against those exact rows (§6 limitation).

Result: **near-zero, mixed-direction effect.**

- Brier delta: t=1 identical (+0.0065 both); t=2 +0.0026 (with) vs. +0.0025 (without).
- AUC: marginally *worse* with the feature included in its degraded state (−0.0004 at t=1,
  −0.0014 at t=2).
- ECE: marginally *worse* with the feature included (+0.0006 at t=1, +0.0007 at t=2).
- **Both configurations pass the ADR-0009 combined shadow gate.**

No significance testing was performed on this delta — flagged as a limitation (§6). The practical
conclusion: the degraded feature is not actively harmful enough to justify retiring it outright,
and is not helping enough in its current state to argue against repairing it. This is exactly the
condition under which repair is the correct call — the cost of being wrong in either direction is
low, so the decision should follow the cheaper, more defensible action (repair, since ~85% of
rows already carry real signal and the failures are mechanical).

---

## 4. Decision: repair, not retire

**REPAIR** `_PARK_FACTOR_HITS`/`_VENUE_NAME_ALIASES` (already implemented, this branch, commit
`b710609`), rather than removing `park_factor_hits` from the feature contract.

Rationale:

1. The failures are mechanical and cheap to fix — one missing dict entry, one wrong exact string,
   several sponsorship renames — not a structural defect in the feature's design or its data
   source.
2. T-575 itself suggested a venue-ID/name fallback repair path as the preferred remedy if the
   dead-feature hypothesis held.
3. The feature already passes the ADR-0009 shadow gate and shows near-zero net cost even in its
   degraded, pre-fix state (§3) — retiring it would discard the ~85% of rows carrying real signal
   to avoid fixing a fixable ~15%.
4. The fix is structurally more robust than a 1:1 string swap: a `_VENUE_NAME_ALIASES`
   indirection layer tolerates the live API returning either an old or a new/full/short venue
   name for the same physical park, rather than betting on one exact string per rename.
5. Previously fully-silent failures (both the unmatched-venue-name path and the
   venue-data-entirely-missing path) are now surfaced via one aggregate
   `park_factor_venue_unmatched` WARNING audit event per `compute_features_bulk` call — this
   defect class cannot recur silently again without leaving an audit-log trace.

**Alternative considered and rejected:** retire `park_factor_hits` from the feature contract
entirely. Rejected because it would sacrifice real, gate-passing signal on the majority of rows
to eliminate a now-understood, now-fixed, and now-monitored minority-case defect.

---

## 5. Activation gate — not authorized by this ADR

This ADR documents and justifies the repair; it does **not** authorize activation. Per ADR-0042
D2, any change to a feature's derivation that alters live scoring behavior going forward requires
clearing the `DEFENSIBLE_IMPROVEMENT` holdout gate before deployment. Activation — redeploying
the corrected `mlb_features.py` to the VPS pipeline so it governs live paper-trading scores —
requires:

1. Operator sign-off on this ADR (Status → ACCEPTED).
2. The ADR-0042 D2 holdout-gate run, evaluated fresh against the corrected feature (not reusable
   from any prior gate pass, since the feature's derivation has changed).
3. A production deploy, which this session is explicitly not authorized to perform.

Until then, the fix exists only on this branch/worktree; T1 MLB's live pipeline continues scoring
with the pre-fix, degraded `_PARK_FACTOR_HITS` table.

---

## 6. Honest limitations

- **Small long tail unresolved.** ~0.4–1% of rows each across 8 other teams (AZ, CHC, COL, PHI,
  STL, CIN, SD, DET) remain unmatched and un-root-caused. Hypothesized as international or
  exhibition-game venues (e.g., Mexico City, London, Seoul series) but not independently
  confirmed. Left unaddressed — the aggregate `park_factor_venue_unmatched` audit event will
  surface these going forward rather than hiding them.
- **Demonstration method pivot.** The task brief asked for a direct replay of the fix against the
  same historical rows. The stored historical CSV does not retain the raw venue-name string
  (only the derived float), and no cached raw C1 `game_starters`/schedule JSON was found locally,
  so a literal historical-row replay was not mechanically possible. This investigation
  substituted live MLB Stats API verification instead — arguably a stronger demonstration that
  the fix resolves against the *current* real API contract, but a deviation from the literal
  request that should be read as such, not silently substituted.
- **No significance testing on the Deliverable 2 delta.** The near-zero with/without difference
  (§3) is reported as a point estimate; no confidence interval or hypothesis test was computed.
- **This ADR does not itself change GG-145's registered text.** That belongs to session/block
  36.3, per this session's explicit scope fence; the corrected finding is handed off via the
  results-summary file, not written directly into the gap log.
