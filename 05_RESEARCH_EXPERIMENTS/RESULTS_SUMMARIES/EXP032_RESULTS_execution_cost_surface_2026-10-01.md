# EXP-032 RESULTS — Execution cost surface (T-603, GG-325)

**Pre-registration:** `05_RESEARCH_EXPERIMENTS/EXP032_EXECUTION_COST_SURFACE_PREREGISTRATION_2026-10-01.md` (frozen at c663f41, pushed alone before any statistic was computed).
**Script:** `scripts/execution_cost_surface.py` · **Tests:** `tests/test_execution_cost_surface.py` (9 pass) · **Raw output:** `exp_output/EXP-032-EXECUTION-COST-SURFACE/{results.json,capacity.json}`.
**Archive:** 2,125,077 price rows, 2026-08-01 → 2026-10-01 (read-only). B, null bands and B's CIs are EXP-031's, taken as given. Settlements are EXP-031's cache; nothing re-fetched. No model, order, sizing or pool touched.

**Headline: no family's E crosses zero under any policy that the archive evidences.** Policies (a) and (c) never do. Policy (b) shows E > 0 for two families (KXMLBF7, KXMLBTEAMTOTAL), but in both the calibration gap B is not present at the cheap entry point, so the positive E is B-from-one-moment minus H-from-another and is not a tradable edge. Neither is labelled CANDIDATE.

## 0. Correctness gates (pre-registered §9, run before anything else)
| Gate | Result |
|---|---|
| Policy (a) recomputes EXP-031 H and E to 1e-5, all 14 families | **PASS** (14/14) |
| Policy (c) with forced fill reproduces EXP-031 B to 1e-5, all 14 families | **PASS** (14/14) |
| Clock sanity gate (close−start median in [2.0, 4.5]h, ≥95% in (0, 8]h) | PASS: F7, GAME, HIT, SPREAD, TEAMTOTAL, TOTAL. **FAIL: F3, F5, F5SPREAD, F5TOTAL** — their markets close 1.0–1.7h after start (shorter games), below the frozen 2.0h floor. The clock itself looks sound (>99% of tickers inside (0, 8]h). Per the pre-registered rule they fall back to "no pregame clock": policy (b) UNMEASURED and drift UNMEASURED, policy (c) run with the close clock and flagged. The floor was not edited after the fact (GG-327). |

## 1. Cost surface and coverage (Deliverable 1)
Full tables (τ, phase, price, τ×price, τ×phase, side, ticks) per family: `results.json → families[*].surface`. A cell is MEASURED only at ≥200 snapshots, ≥30 tickers, ≥5 days; otherwise UNMEASURED and not interpolated. Coverage of the τ×price grid (80 cells):

| Family | measured cells | share of grid | share of snapshots in measured cells |
|---|---|---|---|
| KXMLBTEAMTOTAL | 64 | 80.0% | 99.8% |
| KXMLBTOTAL | 59 | 73.8% | 99.6% |
| KXMLBHIT | 47 | 58.8% | 99.8% |
| KXMLBF5TOTAL | 44 | 55.0% | 99.4% |
| KXMLBF7 | 32 | 40.0% | 97.0% |
| KXMLBSPREAD | 34 | 42.5% | 98.9% |
| KXMLBGAME | 30 | 37.5% | 97.3% |
| KXMLBF5 / F3 / F5SPREAD | 29 / 21 / 24 | 36% / 26% / 30% | ≈98% |
| KXNFLTEAMTOTAL / TOTAL / SPREAD | 56 / 51 / 41 | 70% / 64% / 51% | ≈82–83% |
| KXNFLGAME | 0 | 0% | 0% (only 21.6k rows; no usable cell) |

Measured-cell share is low in absolute terms because the price dimension is thin at the tails; it covers almost all the snapshot mass.

**Shape of H (KXMLBTEAMTOTAL, median half-spread by hours to settlement):** in-play 0.5c · [0,1)h 0.5c · [1,3)h 0.5c · [3,6)h 0.5c · [6,12)h 1.5c · [12,24)h 1.5c · [24,48)h 3.0c (IQR 1.5–16c). KXMLBHIT: 0.5c at [0,6)h, 1.0c at [6,12), 1.5c at [12,24), 2.5c at [24,48). **H is a strong function of time: the toll is lowest in the last hours before the start and highest at the 24–48h horizon, which is where EXP-031's first-seen snapshot disproportionately landed.** The F5SPREAD/F5TOTAL EXP-031 H (27.5c, 14.5c) cannot be re-priced by hours-to-start (clock gate); under the close-clock policy (c) their E rises to −.080/−.065 but stays negative.

**Side.** The archive books are exactly complementary (`no_ask = 1 − yes_bid`, `yes_ask = 1 − no_bid`, zero residual on all 2.125M rows), so YES and NO costs are identical when both sides quote (max |yes_cost − no_cost| = 0). The brief's expectation of separate YES and NO costs is therefore not borne out for price; the difference is **availability**: KXMLBHIT YES is buyable at 90.8% of snapshots but NO at 64.0%; TEAMTOTAL 94.2% vs 96.1%.
**Ticks.** Half-spreads are whole-cent multiples of 0.5c; the 0.5c minimum is a floor, not a fitted value.

## 2. Recomputed E by policy (Deliverable 3; B and null from EXP-031, cost side only)
E = B − null_median − H (a, b) or R_c − null_median (c). CIs: game-cluster; day-cluster in brackets; B's CI is EXP-031's, summed with a cost-side bootstrap by interval arithmetic (conservative, pre-registered §4).

| Family | EXP-031 E | (a) first-seen | (b) cheapest MEASURED (τ\*) | (c) rest at mid, evidenced fills only (fill rate) | Label |
|---|---|---|---|---|---|
| KXMLBF5SPREAD | −.198 | −.198 [−.229,−.162] | UNMEASURED (clock gate) | −.080 [−.091,−.069] (39%) | NO |
| KXMLBF3 | −.144 | −.144 | UNMEASURED | −.099 (43%) | NO |
| KXMLBF5 | −.129 | −.129 | UNMEASURED | −.090 (54%) | NO |
| KXMLBF7 | −.167 | −.167 [−.176,−.147] | **+.023 [+.019,+.038]** [0,1)h, H=1.0c | −.037 [−.046,−.027] (25%) | **B-NOT-EARNED-AT-ENTRY**: B_entry .038, E_entry −.0013 |
| KXMLBF5TOTAL | −.095 | −.095 [−.146,−.028] | UNMEASURED | −.065 [−.081,−.050] (54%) | NO |
| KXMLBTEAMTOTAL | −.024 | −.024 [−.041,−.013] | **+.011 [+.004,+.022]** [0,1)h, H=0.5c | −.023 [−.028,−.018] (23%) | **B-NOT-EARNED-AT-ENTRY**: B_entry .0228 vs null .0218, E_entry +.0009 |
| KXMLBGAME | −.039 | −.039 | −.004 | −.020 [−.044,+.005] (67%) | NO (does not clear null) |
| KXMLBSPREAD | −.011 | −.011 | −.006 | −.013 (15%) | NO |
| KXMLBTOTAL | −.012 | −.012 | −.002 | −.013 (36%) | NO |
| KXNFLGAME / SPREAD / TEAMTOTAL / TOTAL | +.037 / −.031 / −.009 / −.013 | same | UNMEASURED (no NFL start time) | +.022 / −.038 / −.054 / −.095 (fill 93–96% / 93% / 70% / 71%; **not pregame-clean**, see below) | NO |
| **KXMLBHIT (reference)** | −.0008 | −.0008 [−.006,+.005] | +.0042 [−.0006,+.0101] [0,1)h | −.0052 [−.0066,−.0037] (10%) | NEAR; B_entry .018 earned, but CI spans zero and day-fragile |

**Does any E cross zero under an evidenced policy, and by how much?** Under (a): none (best KXMLBHIT −.0008, CI spans zero; KXNFLGAME +.037 does not clear its null and its game-cluster CI is [−.03,+.17]). Under (c): none. Under (b): F7 +.023 and TEAMTOTAL +.011 have positive CIs, but fail the pre-registered B-at-entry check: at the [0,1)h entry point the calibration gap is smaller (.038 vs .050 for F7; .0228 vs .0257, indistinguishable from the null for TEAMTOTAL), and at the entry-matched B the E is −.001 and +.001, with no CI separation from zero. KXMLBHIT under (b) is the closest to the line: +.0042, CI [−.0006,+.0101] (game) / [−.0002,+.0109] (day), B earned at entry; this is NEAR, a result that could be noise, and is not promoted.

**What this shows.** The H in EXP-031 was a first-look toll, and H falls an order of magnitude as the start approaches (measured for F7: 20c → 1c; TEAMTOTAL 4c → 0.5c). But B falls as well: the mispricing EXP-031 measured at the earliest quote mostly has already converged by the time the toll is cheap. The cost-side correction removes the kill for the families that EXP-031 killed by H alone, and then B at the cheap entry point kills them (or leaves them indistinguishable from the null).

**NFL caveat.** NFL tickers carry no start time; policy (c) fills are searched before market close, which may include in-play quotes. The 93–96% fill rates on KXNFLGAME/SPREAD are a symptom (a sample of 21.6k rows), not evidence of liquidity.

## 3. Capacity (Deliverable 4)
Only KXMLBF7 and KXMLBTEAMTOTAL reached policy-(b) E > 0, and both carry the entry-B label; capacity is reported for them and for the reference. The depth archive is a sample: F7 = 6 rows over 1 ticker; TEAMTOTAL 2,413 rows over 361 tickers; HIT 1,889 rows over 761 tickers.

| Family | depth rows / tickers | p25 of USD within 5c on the thinner side | supports $5 / $25 / $100 / $500 stake at 5× coverage |
|---|---|---|---|
| KXMLBF7 | 6 / 1 | 0 | **cannot say** (sample insufficient) |
| KXMLBTEAMTOTAL | 2,413 / 361 | $0.00 | no at every size (the sample's lower quartile is zero depth) |
| KXMLBHIT | 1,889 / 761 | $6.54 | no at every size (5× of $5 is $25) |

Had either family earned CANDIDATE, the label would have been CANDIDATE-PENDING-CAPACITY. The depth sample does not support any stake in this project's range for these three families; it can describe nothing about a stake larger than the depth sampler's lower quartile.

## 4. Drift between first-seen and settlement (Deliverable 5)
**This is not T-569.** T-569 tested a ~60s in-play T4 latency thesis and returned NOT SUPPORTED. This measures hours-to-days pregame drift between the first-seen quote (≥6h before start) and the last pregame snapshot (≥1h later). The two are different claims. Resemblance to report rather than bury: KXMLBHIT is T-569's cell, and its result here (forward slope +.0014 against a backward slope −.018) is also a null, at a different horizon.

Pairs: HIT 5,599; TEAMTOTAL 9,874; TOTAL 7,790; SPREAD 4,260; F7 2,045; GAME 1,542. Slope of drift on (p_first − .5); backward placebo is the time-reversed series (T-569/EXP-029 convention).

| Family | forward slope | backward slope | placebo ratio | passes T-569 rule (ratio <0.5 or backward CI ∋ 0) |
|---|---|---|---|---|
| KXMLBTEAMTOTAL | +.108 | −.227 | 2.10 | no |
| KXMLBTOTAL | +.036 | −.056 | 1.55 | no |
| KXMLBSPREAD | +.035 | −.087 | 2.53 | no |
| KXMLBHIT | +.0014 | −.018 | 12.8 | no |
| KXMLBF7 | −.039 | −.543 | 13.9 | no |
| KXMLBGAME | −.007 | −.199 | 30.0 | no |

**Every placebo ratio is above 1 (EXP-029's was 1.02).** The time-reversed series shows a larger apparent effect than the forward one, with the opposite sign. That is the signature of a mechanical regression-to-the-mean artefact of conditioning on an endpoint, not of information. No forward drift claim survives. (The "CLV" statistic — drift in the direction of EXP-031's bucket sign — is positive for TEAMTOTAL (+.030, CI [+.025,+.035]) and HIT (+.005), and its backward counterpart is negative, but with the placebo failing, I do not read it as evidence.) The drift test cannot be run for F3/F5/F5SPREAD/F5TOTAL (clock gate) or NFL (no start time).

## 5. Is the toll structural, or an artefact of when we looked?
Mostly the latter for the *size* of the toll, and neither for the question that matters. The 20c half-spread EXP-031 charged KXMLBF7 was a real quote but the earliest one, 24–48h out; the same market quotes ~1c within an hour of the start (the other F-series cannot be re-priced by hours-to-start, see §0). So the kill-by-H result is an artefact of measuring cost at one moment. What the cost-side recompute does not rescue is the edge: at the cheap moment the calibration gap that B measured at the first look has largely closed (F7, TEAMTOTAL: entry-matched E ≈ 0), and the pregame price drift that would explain the closure fails its placebo, so I cannot say how it closes. The structural part of the toll is a floor of 0.5c half-spread (1c vig) on every liquid MLB cell, plus one-sided books (YES-only on 36% of HIT snapshots), plus depth too thin to size on. That is a finding about these MLB families in these 60 days and about what the archive can evidence. It is not a finding about the rest of the board, and it is not a recommendation against any sport or family.

## 6. Not measurable, and why
- 6–12h-to-close capture hole: cells exist but are thin (e.g., HIT [6,12)h 1,717 snapshots against 44,926 at [12,24)h); the capture defect is owned by 44.3 and GG-325 depends on it.
- NFL: no start time, so no pregame clock, no policy (b), no drift; settlement-cache coverage 76–86%.
- F3/F5/F5SPREAD/F5TOTAL: clock gate failed (GG-327), so (b) and drift UNMEASURED.
- Fills are evidenced only by a strictly-through opposite quote in a later pregame snapshot; the archive is ~20-minute snapshots, so a fill between snapshots is invisible and (c)'s fill rate is a lower bound. The unfilled counterfactual is in `results.json` but is not credited.
- Depth: sample only.
- 60 days of one season's late-year slate; the day-fragile flags carry over from EXP-031.
