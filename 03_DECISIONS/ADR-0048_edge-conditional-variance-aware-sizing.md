# ADR-0048: Edge-Conditional, Variance-Aware Sizing (Supersedes ADR-0040)

**Status:** PROPOSED — awaiting operator/DS sign-off. No live parameter in `execution_bands.py` or `risk.py` is changed by this document. Per Hard Rule 3, ADR-0040 is not edited in place; this document supersedes it.
**Date:** 2026-07-28
**Author:** Session `session/20260728T234000Z-b3-sizing` (Window B3, `ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md`)
**Supersedes:** ADR-0040 (`03_DECISIONS/ADR-0040_ruin-risk-remediation-kelly-derating.md`, ACCEPTED 2026-07-04)
**Depends on:** GG-135 (OPEN), GG-105 (OPEN), B2 frontier (`05_RESEARCH_EXPERIMENTS/MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md`), D2 gate (`scripts/mc_empirical_bootstrap.py`)

---

## 1. Why ADR-0040 must be superseded, not amended

ADR-0040 (2026-07-04) de-rated `T1_MULTI_DAY.kelly_fraction` from 0.10 to 0.061, computed to hold 1yr P(kill) ≤ ~5.6%. That derivation was explicitly conditional on a real, measured edge: a 53.06% win rate, modeled as a fixed-parameter IID +EV coin via `mc_forward_projection.py`. The derivation was correct given that premise.

The premise no longer holds, for two independent reasons, both discovered after ADR-0040 shipped:

1. **GG-105 (anti-predictive edge-tercile ranking).** T1/T2/T3 (MAIN) and T4M-PROJ do not show a validated positive, rank-ordered edge. Windows A2 (Platt refit on A1-shrunk features) and A3 (isotonic recalibration) were both run as remediation attempts against MAIN's real resolved ledger and **both explicitly FAILED** the monotonicity gate criterion (DECISION_LOG.md, 2026-07-24):
   - A2: Fisher p=0.2115, `winrate(edge>0)=0.475 < winrate(edge≤0)=0.580`, inverted terciles (0.593/0.385/0.505) — marginally *more* inverted than baseline (p=0.6223).
   - A3: Fisher p=0.1289, `winrate(edge>0)=0.470 < winrate(edge≤0)=0.593`, essentially the same inverted shape (0.593/0.396/0.495).
   - Both passed calibration-slope and Brier/ECE criteria — the *magnitude* of the probability estimates is fine. The *rank order* is not.
   - **Structural conclusion:** Platt scaling and isotonic regression are both monotonic transforms of the same underlying model score. A monotonic transform cannot invert or reorder a ranking. If the underlying score's rank order is already wrong, no monotonic recalibration method can fix it. This is not a tuning failure — it is evidence the defect lives upstream, in the feature/model itself, not in the calibration layer. Fixing it requires a genuine feature or model change (candidate: T-384/H2, blending `p_t1` into the shrinkage prior), gated on DS sign-off, not yet actioned.

2. **GG-135 (variance alone kills MAIN regardless of edge sign).** `mc_empirical_bootstrap.py` (D2), replaying MAIN's real resolved bets rather than assuming a fixed win rate, found all three available cohorts — strict epoch-8 (−0.062%/bet), post-fix e6-8 (−0.001%/bet), full-history (+0.006%/bet) — hit the 20%-drawdown kill switch at ~85.8%-100% within 30-365 days. MAIN's real per-bet σ (1.081%) combined with its real cadence (15.83 bets/day) is large enough that a **zero-edge** MAIN book self-terminates at today's sizing almost as surely as a negative-edge one. The B2 frontier sweep (`MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md`) quantifies this: MAIN needs +0.169%/bet just to hold 1yr P(kill) ≤ 10% at today's config — roughly 27× the best-ever observed cohort mean (+0.006%/bet).

Taken together: ADR-0040's ~5.6% 1yr breach figure was never wrong on its own terms, but its terms (a real 53.06% edge) are not the world we are in. There is currently no validated positive, rank-ordered edge on MAIN or T4M-PROJ to size for. **A point-estimate Kelly de-rating computed against an edge that may not exist is not a fix — it is a number attached to the wrong premise.** This ADR replaces that premise with an explicit edge-conditional framework: sizing is a function of *validated* edge, not an assumption of it, and the function's value at zero/unvalidated edge is zero.

---

## 2. Decision

**Sizing becomes edge-conditional.** For every MAIN-book-model band (T1_MULTI_DAY, T2_SAME_DAY, T3_PRE_TIP) and for T4M_PROJ, the live `kelly_fraction` is not a single derated constant — it is looked up against the validated per-bet edge currently in force for that band, per the table in §3. **The default entry in that table, in force today, is edge=0/unvalidated → kelly_fraction=0 (no live sizing; no new paper bets deployed at nonzero stake).**

This is a precondition, not a parallel input: positive, rank-order-validated edge (i.e., GG-105 resolved for that band, and a re-run of the monotonicity gate criterion passing) is a **gate that must be satisfied before any nonzero Kelly fraction is read from the table** — not a factor that can be netted against sizing math independent of the gate.

### 2.1 Current operating point (as of this ADR, 2026-07-28)

| Band | Real per-bet edge (strict-e8, `MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md`) | GG-105 monotonicity gate | Sizing under this ADR |
|---|---:|---|---|
| T1_MULTI_DAY | −0.062%/bet (MAIN cohort) | FAIL (A2/A3) | **kelly_fraction = 0** |
| T2_SAME_DAY | (MAIN cohort, shared model defect) | FAIL (shared MAIN edge signal) | **kelly_fraction = 0** |
| T3_PRE_TIP | (MAIN cohort, shared model defect) | FAIL (shared MAIN edge signal) | **kelly_fraction = 0** |
| T4M_PROJ | −0.012%/bet (T4 strict-e8 cohort) | GG-105 originally discovered here; not separately re-tested by A2/A3 (those ran against MAIN only, per DECISION_LOG.md 2026-07-24 scoping note) | **kelly_fraction = 0** |

T2_SAME_DAY and T3_PRE_TIP are Phase 7 (not yet cron-active) — this ADR states their sizing explicitly rather than leaving it implicit, since GG-105's defect is in the shared C3 model/edge signal they would inherit on activation, not something specific to T1's cron schedule.

T4M_PROJ is included despite GG-105 being originally discovered there and not being in A2/A3's tested scope (those gates ran against MAIN's ledger only — DECISION_LOG.md 2026-07-24 scoping note: T4M-PROJ's `model_p` is a self-contained Binomial calc, not produced by C3). Its own strict-e8 cohort reads −0.012%/bet, below the B2 frontier's own −0.0005%/bet survivability threshold for T4 at today's sizing (headline MC: 56.4%/100%/100%/100% P(kill) at 30/90/182/365 days). Leaving T4M-PROJ at nonzero size while zeroing MAIN, when GG-105 originated on T4M-PROJ and its own current edge reading fails its own survivability threshold, would be inconsistent. **This is a judgment call by this ADR's author, not dictated by the B3 task instruction, and is flagged for explicit operator/DS confirmation or override at sign-off. Operator confirmed 2026-07-28 ("Agree on both - I accept") — no override.**

**Practical effect:** no new capital is put at risk on any of these four bands while at the default table entry. This is a sizing-side mitigation for GG-135's ruin risk, applied uniformly, while GG-105's modeling defect remains open and unresolved on its own separate remediation track.

---

## 3. Reactivation lookup table (against B2 frontier, not a hardcoded number)

This table is the sizing function. It is read only once a band's GG-105 monotonicity gate re-run (methodology in DECISION_LOG.md 2026-07-24 A2/A3 entries: Fisher exact test on edge-tercile win rates, direction and significance both checked, AND'd with calibration-slope-CI-includes-1.0 and Brier/ECE-vs-baseline criteria) **passes** for that band, against the newly-validated per-bet edge `X` reported by that gate re-run. Interpolate conservatively (round down to the next-lower bracket) if the validated edge falls between rows.

### MAIN book (T1_MULTI_DAY / T2_SAME_DAY / T3_PRE_TIP) — source: B2 Part A/B, real σ=1.081%, real cadence=15.83 bets/day

| Validated per-bet edge `X` | Max Kelly-fraction multiplier (of ADR-0010's 0.10/0.13/0.07 baseline) | Max cadence multiplier | Min DD-kill width | Resulting 1yr P(kill) |
|---:|---:|---:|---:|---:|
| Not validated / GG-105 open | **0×** (kelly_fraction=0) | n/a — no deploy | n/a — no deploy | n/a — no deploy |
| 0.00%/bet (edge validated as flat) | 0.10× | none up to 10× cut helps | none up to 50% helps | ≤10% only via Kelly cut |
| +0.02%/bet | 0.10× | none up to 10× cut helps | none up to 50% helps | ≤10% only via Kelly cut |
| +0.05%/bet | 0.25× | none up to 10× cut helps | 50% | ≤10% |
| +0.10%/bet | 0.50× | none up to 10× cut helps | 30% | ≤10% |
| +0.169%/bet (B2 Part A breakeven-to-target threshold) | ~0.61× (≈ADR-0040's derived 0.061 absolute value off the 0.10 baseline) | n/a | 20% (current) | ≤10% |
| +0.20%/bet | **1.00× (ADR-0010 original)** | 3.0× | 20% (current) | ≤10% |

**Reading this table:** at any validated edge below +0.169%/bet, the B2 frontier's structural finding governs — cadence throttling and drawdown-width widening are order-of-magnitude too weak to matter (variance scales quadratically with Kelly multiplier, only linearly with cadence, and DD-width doesn't touch variance at all; see B2 §"non-obvious structural finding"). **Kelly-fraction reduction is the only lever with enough leverage to restore survivability** at MAIN's real variance shape. Do not substitute a cadence or DD-width change for a Kelly cut at these edge levels.

### T4 book (T4M-PROJ) — source: B2 Part A/B, real σ=0.041%, real cadence=67.09 bets/day

| Validated per-bet edge `X` | Max Kelly-fraction multiplier (of ADR-0023's 0.10 baseline) | Max cadence multiplier | Min DD-kill width |
|---:|---:|---:|---:|
| Not validated / GG-105 open | **0×** (kelly_fraction=0) | n/a — no deploy | n/a — no deploy |
| 0.00%/bet | 1.5× | 3.0× | 15% |
| +0.02%/bet | 3.0× (grid ceiling — true headroom above this not measured by B2) | 3.0× | 10% |
| +0.05%/bet | 3.0× (grid ceiling) | 3.0× | 10% |
| +0.10%/bet | 3.0× (grid ceiling) | 3.0× | 10% |
| +0.20%/bet | 3.0× (grid ceiling) | 3.0× | 10% |

T4 is, per B2's own read, **edge-limited, not ruin-limited** — its σ is ~26× smaller than MAIN's, so once GG-105 is resolved for T4M-PROJ and any positive edge is validated, sizing headroom is large. The binding constraint for T4M-PROJ is GG-105 itself, not the sizing table.

---

## 4. Precondition framing (why this is a gate, not a formula input)

`MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md` established that MAIN's real variance geometry alone — independent of edge sign — produces near-100%/yr kill probability at today's sizing for cohorts reading between −0.062% and +0.006% per bet. GG-135 (OPEN) registers this as a structural finding: the risk configuration self-terminates before the statistical test it exists to run (G6's `clean_n ≥ n*` sample-adequacy gate, GG-004/APR-0024) can complete.

This means sizing cannot be computed as `f(assumed edge)` where "assumed edge" is a free parameter a future session might plug in optimistically. It must be computed as:

```
kelly_fraction(band) =
    0                                     if GG-105 monotonicity gate has not passed for band
    lookup(§3 table, validated_edge)      if GG-105 monotonicity gate has passed for band,
                                           using the edge value the passing gate run itself reported
```

The gate-pass is not a one-time unlock after which any edge number can be assumed indefinitely — each reactivation is tied to the specific validated edge figure the passing gate run reported, and re-verification (fresh D2 run, §5) is required before that number is trusted for a live sizing decision.

---

## 5. D2 gate requirement for any future nonzero reactivation

Before any band's `kelly_fraction` is moved off 0 in `execution_bands.py`, both of the following must be satisfied and recorded in a new DECISION_LOG.md entry:

1. **GG-105 monotonicity gate passes** for that band, on a cohort meeting GG-004's `clean_n ≥ n*` sample-adequacy standard (not an epoch-proxy substitute, per the open item registered 2026-07-24 re: epoch-8's stale-corpus unmatchability) — reporting a specific validated per-bet edge `X`.
2. **A fresh `scripts/mc_empirical_bootstrap.py` (D2) run**, using the §3 table's Kelly-fraction/cadence/DD-width values looked up against that validated `X`, confirms 1yr P(kill) at or below the target threshold (10%, consistent with B2's derivation standard) for that specific band's real cadence and variance shape at time of re-run — not the B2 sweep's illustrative brackets taken as given, since real σ/cadence may have drifted since 2026-07-23.

Sizing does not go live on the strength of the lookup table alone; the table sets the candidate configuration, D2 re-confirms it against then-current real data before deploy. The zero-size default state trivially satisfies D2 (a book placing no bets cannot be killed by variance), so no D2 run is required to remain at the default.

---

## 6. Open items (not resolved by this ADR)

- **G6 accrual while at zero size.** MAIN/T1 and T4M-PROJ paper-bet accrual toward G6's 30-resolved-bet count halts while `kelly_fraction=0` (no new bets placed). Whether this pauses the G6 clock, requires a separate accrual mechanism, or requires an explicit operator decision to accept slower gate progress is **not decided by this ADR** and requires DS/operator judgment. **Operator confirmed 2026-07-28 ("Agree on both - I accept"): accepts slower G6 gate progress — the clock pauses while `kelly_fraction=0`; no separate accrual mechanism will be built.**
- **GG-105's own remediation path** (candidate T-384/H2: blend `p_t1` into the shrinkage prior) is a separate, not-yet-actioned task. This ADR does not propose or gate that work; it only states that until GG-105 resolves, this ADR's zero-size default is the correct operating point for the bands listed in §2.1.
- **T4M-PROJ inclusion (§2.1)** is this ADR author's judgment call, flagged explicitly for operator/DS override at sign-off — the original B3 task scope was MAIN/T1-focused; extending the zero-default to T4M-PROJ was not explicitly instructed and should be confirmed, not silently accepted. **Operator confirmed 2026-07-28 ("Agree on both - I accept") — no override; T4M-PROJ stays at `kelly_fraction=0` per §2.1.**
- **Code change is NOT made by this document.** If accepted, `execution_bands.py`'s `T1_MULTI_DAY`, `T2_SAME_DAY`, `T3_PRE_TIP`, and `T4M_PROJ` `kelly_fraction` fields must be edited to 0 (or an equivalent no-deploy gate enforced upstream in the execution engine) in a separate, explicitly-authorized follow-up change — per ADR-0040's own precedent ("this ADR does not change any live parameter by itself").

---

## 7. Relationship to ADR-0040

ADR-0040's sensitivity-analysis methodology (cadence de-rating, formal P(kill)-target search, cap-lowering comparison) and its finding that cap-lowering alone has zero effect at the 30-day horizon are **not invalidated** — they remain valid analysis of the positive-edge case. What is superseded is the *application* of that analysis as the operative sizing rule for MAIN going forward, since its premise (a real 53.06% edge) is not currently validated. ADR-0040's 0.061 figure survives in this ADR's lookup table (§3, MAIN row at +0.169%/bet) as the sizing value to use *if and when* an edge near that magnitude is validated — it is repositioned from "the current rule" to "one row in a lookup table gated on validation," not deleted.

---

## 8. Addendum (2026-07-28, T9/`session/20260729T050047Z-t9-rework`) — completing the aux-computation cascade

**Status of this addendum: PROVISIONAL & NON-OPERATIONAL, same as the rest of this document.** No live parameter changes here either. Appended rather than filed as a new ADR because §3-§5 above already establish the governing structure (edge-conditional lookup + gate) that this addendum extends, not replaces; appended rather than edited in place per this project's standing practice of not silently rewriting a document another session (and the operator, per the three inline confirmations above) has already reviewed.

**Why this addendum exists:** T9's task scope (GG-105 rework + sizing-bucket foundation) required the auxiliary-computation cascade to name five co-dependent mechanisms explicitly: Kelly fraction, per-bet exposure cap, drawdown kill-switch width, daily-loss breaker, and the ADR-0026 portfolio free-cash/deployment invariant. §3's table above already covers Kelly-fraction multiplier and DD-kill width. It is silent on the other three. This addendum fills that gap — it does not change §2's operating point (all bands still `kelly_fraction=0`; T9's own A1-A3 work below confirms GG-105 is still OPEN for MAIN, so nothing here unlocks anything).

**T9 context feeding this addendum:** T9's Part A (`exp_output/T9_GG105_REWORK/`, DECISION_LOG.md 2026-07-28) ran a feature-level discrimination check one level below A2/A3's calibration-transform tests — joining MAIN's real resolved ledger to the historical C2 feature matrix by `(player_id, game_date)`, n=313. Finding: no individual raw pregame feature clears the monotonicity bar (alpha=0.10), and a market-relative proxy mirroring the live model's own edge logic (`ba_l10_shrunk - mip`) is *strongly* anti-predictive (Fisher p<0.0001) — confirming GG-105's defect lives in the feature/model layer, not just surviving through calibration, one level deeper than A2/A3 had shown. A scoreable non-monotonic candidate (CV-fit logistic interaction on `bb_rate_l10`) was proposed and scored via this same D1 harness and **also FAILED** (ANTI-PREDICTIVE, Fisher p<0.0001, worse Brier than baseline). GG-105 remains OPEN; §2's zero-size default remains the correct operating point. See T9 DONE entry, DECISION_LOG.md, for the full result.

### 8.1 Per-bet exposure cap — a market-depth ceiling, not a variance-derived one

`max_single_event_exposure_usd=500.0` (`risk.py` `_HARD_LIMITS`) is not on the same derivation axis as Kelly fraction: it is a **market-depth backstop** (CLAUDE.md's Kalshi KXMLBHIT depth note: $500-$2,000/market, implying $50-$250/bet stays within depth), not a variance-survivability figure. It does not need its own row in §3's edge lookup. But it is not independent of that lookup either — it is the **other operand of a `min()`**:

```
per_bet_stake(band, X) = min(
    kelly_stake(band, lookup(§3 table, X)),   # variance-survivability leg
    max_single_event_exposure_usd,             # market-depth leg (unchanged by X)
)
```

At every row in §3's current tables, `kelly_stake` is small enough that the depth cap does not bind (verify at reactivation time, §5). **The cascade dependency to watch:** at MAIN's top table row (+0.20%/bet, 1.00× Kelly multiplier) or T4's grid-ceiling rows (3.0× multiplier), re-derive `kelly_stake` against the then-current bankroll before assuming the depth cap still doesn't bind — a materially larger bankroll than at ADR-0040's 2026-07-04 baseline could push `kelly_stake` above $500 well before Kelly fraction itself looks large, silently making the depth cap (not the Kelly math) the actual sizing constraint. This should be an explicit check inside the §5 D2 gate re-run, not an assumption carried forward from this table.

### 8.2 Daily-loss breaker — must be re-validated at higher Kelly multipliers, not held fixed

`MAX_DAILY_LOSS_PCT=0.15` (`risk.py`) is denominated in % of session-start bankroll and was calibrated against MAIN's *current* per-bet σ/cadence at the *current* (already-zeroed, or historically 0.10 baseline pre-ADR-0040) Kelly fraction. It is not automatically correct at every row of §3's lookup: **daily P&L variance scales with the Kelly multiplier applied to each bet, and cadence multiplier compounds it** (both levers §3 explicitly varies as validated edge `X` rises). A 15% daily breaker calibrated for baseline sizing can either (a) become too tight at higher Kelly multipliers — false-tripping on ordinary variance from a book that is legitimately sized up because edge was validated — or (b) in the unlikely case a future edge reading is very large, too loose relative to the same-day loss a fat-tailed session could produce.

**Cascade rule:** any table row in §3 with Kelly-fraction multiplier above the "0.10× (unchanged)" default rows requires the §5 D2 re-run to *also* report the simulated daily P&L distribution at that row's Kelly/cadence multipliers and confirm 0.15 still sits at a sane percentile of that distribution (not just confirm 1yr P(kill) ≤ 10%, which is a different statistic). If the simulated daily distribution says otherwise, `MAX_DAILY_LOSS_PCT` must be re-derived alongside the Kelly-fraction reactivation, not left at 0.15 by default. This is a genuine open dependency, not yet computed for any row above the default — flagged here so a future reactivation session doesn't skip it.

### 8.3 ADR-0026 portfolio deployment invariant — a cross-band aggregate, checked when cadence rises

ADR-0026's two-tier free-cash/deployment invariant (`max_portfolio_deployment_pct` in `_HARD_LIMITS`) caps *aggregate* capital-in-flight across all simultaneously-open positions, not any single band's per-bet math — so it cannot be a row in §3's per-band table. It is nonetheless part of the cascade because §3's **cadence multiplier** (up to 10× for MAIN, 3.0× for T4) directly increases average capital-in-flight at a fixed per-bet stake, and combines multiplicatively with any Kelly-fraction increase: more bets open simultaneously, each larger, is exactly what the deployment invariant exists to cap.

**Cascade rule:** any table row with a cadence multiplier greater than 1.0× must have the §5 D2 gate re-run include a portfolio-level capital-in-flight simulation (not just the existing per-bet/per-day P&L simulation) checked against `max_portfolio_deployment_pct`, for both MAIN (up to 10× cadence) and T4 (up to 3.0× cadence). If the deployment invariant would bind before the row's nominal Kelly/cadence combination is reached, the invariant — not the table row — is the actual sizing ceiling at that edge level, and the effective cadence multiplier used at reactivation must be capped accordingly. This has not been computed for any row above 1.0× cadence in either table; it is a required step at reactivation time, not a settled fact.

### 8.4 Net effect on §4/§5's activation gate

None of §8.1-§8.3 changes §4's gate logic (`kelly_fraction(band) = 0 unless GG-105 passes`) or §5's requirement that a fresh D2 run confirm survivability before any nonzero size goes live. They extend what "a fresh D2 run" must check: **exposure-cap bindingness (8.1), daily-breaker sanity at the row's Kelly/cadence multipliers (8.2), and portfolio-deployment bindingness at the row's cadence multiplier (8.3)** are now explicit required outputs of any future §5 D2 re-run, alongside the existing 1yr-P(kill)-≤-10% check. A reactivation that only re-confirms the 1yr P(kill) figure without checking 8.1-8.3 has not fully satisfied §5.
