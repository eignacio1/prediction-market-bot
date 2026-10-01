# EXP-033 Results — Multi-Leg Coherence (2026-10-01)

**Nothing survives.** Of 24 pre-registered cells, 0 are SURVIVES (Holm-adjusted p = 1.0 in every cell). 5 are NO NET VIOLATION; 19 are NOT DISTINGUISHABLE FROM TIMING/COST. No cell was INCONCLUSIVE or DROPPED.

Pre-registration: `05_RESEARCH_EXPERIMENTS/EXP033_MULTILEG_COHERENCE_PREREGISTRATION_2026-10-01.md`, frozen and pushed alone at c9143b1 before any statistic was computed. Amendments: none. Script: `scripts/multileg_coherence.py` (arithmetic only; no model fitted). Artifacts: `exp_output/EXP-033-MULTILEG-COHERENCE/` (d1_grouping.json sha256 `223b7e3d…06bb`, matches the pre-registration).

**D0 SHAs:** before = origin/main c663f41 (this branch at 60f6423+c663f41 sync); pre-registration commit c9143b1; after = see final commit in the branch log.

## D1 — Leg sets and how grouping was verified
Grouping comes from Kalshi metadata (event `mutually_exclusive`, market `strike_type`/`floor_strike`, `custom_strike` team/player uuids, event `sub_title`). The event-ticker suffix is only a join key, confirmed against `sub_title` and team uuids. 84,786 archived tickers, 0 absent from metadata.

| Relation | Sets |
|---|---|
| Complementary: MLB GAME / F3 / F5 / F7 / NFL GAME | 784 / 760 / 760 / 765 / 79 |
| Nested ladders: F5SPREAD 1520, F5TOTAL 760, HIT 13137 (11509 testable), SPREAD 1540, TEAMTOTAL 1540, TOTAL 769, NFLSPREAD 128, NFLTEAMTOTAL 128, NFLTOTAL 64 | |
| Nested cross-family: F5SPREAD<=F5 3040, F5TOTAL<=TOTAL 3794, SPREAD<=GAME 6683, TEAMTOTAL<=TOTAL 9138, NFLSPREAD<=NFLGAME 1727, NFLTEAMTOTAL<=NFLTOTAL 366 | |
| Related | counted, not tested |

Families per game key: {1:28, 3:49, 4:64, 7:1, 8:1, 9:18, 10:878}. **Excluded and counted:** F5TOTAL cross_floor_unmatched 1,589; TEAMTOTAL 1,642; NFLTEAMTOTAL 1,398; HIT single-rung ladders 3. Settled ME sets with exactly one YES: MLB GAME 780, F3 757, F5 756, F7 760, NFL GAME 48. NFL GAME is treated as non-exhaustive (tie possible), so buy-all-YES is not tested there.

## Line-by-line against the pre-registration
| Pre-registered item | Done | Note |
|---|---|---|
| Group by metadata, not ticker strings | Yes | 0 unverified groupings; uncertain excluded and counted |
| Complementary, nested, related relation types | Yes | related counted only |
| Same-run window (identical `run_ts`, active, ask in (0,1)) | Yes | intra-run skew unmeasurable, see Gaps |
| Net of ask-side crossing and ADR-0016 fee | Yes | fee is the in-repo model, not a verified venue constant |
| H sensitivity (mid ± EXP-031 H) | Yes | reported as `net_pos_H_sens`; sensitivity only |
| Timing placebo (prev/next run, fair coin) | Yes | degenerate, see Disclosures |
| Sign-flip over games, 10,000 flips, seed 20261001, one-sided | Yes | |
| Holm over m = 24 | Yes | |
| Persistence ≥ 2 consecutive runs | Yes | |
| Bootstrap 2,000 resamples | **No** | pre-registered, not implemented in `measure`; nothing survived so no CI was needed for a verdict, but this is a deviation |
| Label order INCONCLUSIVE, DROPPED, NO NET VIOLATION, NOT DISTINGUISHABLE, SURVIVES | Yes | |
| Duplicate-row check | Yes | 0 |

## D3 — 24 cells
Columns: games, observations, gross violations, net violations (after toll), net under H sensitivity, placebo net count, persistent observations, max positive margin, Holm p.

| Relation | Family | Dir | Games | Obs | Gross | Net | Net(H) | Placebo | Persist | Max margin | p_Holm | Label |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| complementary | KXMLBF3 | buy_all_no | 759 | 18553 | 271 | 2 | 0 | 155 | 2 | 0.0031 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| complementary | KXMLBF3 | buy_all_yes | 759 | 18553 | 678 | 5 | 0 | 230 | 0 | 0.0114 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| complementary | KXMLBF5 | buy_all_no | 760 | 19526 | 255 | 1 | 178 | 424 | 0 | 0.0046 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| complementary | KXMLBF5 | buy_all_yes | 760 | 19526 | 235 | 2 | 0 | 505 | 0 | 0.0061 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| complementary | KXMLBF7 | buy_all_no | 757 | 19462 | 129 | 4 | 0 | 179 | 0 | 0.0026 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| complementary | KXMLBF7 | buy_all_yes | 757 | 19462 | 206 | 2 | 0 | 314 | 0 | 0.0095 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| complementary | KXMLBGAME | buy_all_no | 784 | 58433 | 493 | 0 | 16 | 879 | 0 | None | 1.0 | NO NET VIOLATION |
| complementary | KXMLBGAME | buy_all_yes | 784 | 58433 | 897 | 1 | 9 | 836 | 0 | 0.0056 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| complementary | KXNFLGAME | buy_all_no | 79 | 10798 | 39 | 0 | 0 | 100 | 0 | None | 1.0 | NO NET VIOLATION |
| nested | KXMLBF5SPREAD | mono | 760 | 39573 | 8 | 7 | 0 | 389 | 2 | 0.0074 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBF5SPREAD<=KXMLBF5 | mono | 760 | 78981 | 7 | 5 | 0 | 678 | 0 | 0.0893 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBF5TOTAL | mono | 758 | 19534 | 4 | 3 | 19 | 408 | 3 | 0.0015 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBF5TOTAL<=KXMLBTOTAL | mono | 760 | 93013 | 0 | 0 | 0 | 42 | 0 | None | 1.0 | NO NET VIOLATION |
| nested | KXMLBHIT | mono | 706 | 96378 | 1 | 1 | 1682 | 12 | 0 | 0.0169 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBSPREAD | mono | 768 | 44456 | 6 | 2 | 203 | 1474 | 0 | 0.0066 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBSPREAD<=KXMLBGAME | mono | 763 | 137067 | 3 | 2 | 3 | 1206 | 0 | 0.0369 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBTEAMTOTAL | mono | 768 | 44498 | 13 | 13 | 245 | 1214 | 4 | 0.0097 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBTEAMTOTAL<=KXMLBTOTAL | mono | 765 | 235868 | 3 | 3 | 57 | 166 | 0 | 0.0159 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXMLBTOTAL | mono | 768 | 22660 | 4 | 0 | 146 | 1371 | 0 | None | 1.0 | NO NET VIOLATION |
| nested | KXNFLSPREAD | mono | 64 | 11573 | 48 | 1 | 22 | 421 | 0 | 0.0309 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXNFLSPREAD<=KXNFLGAME | mono | 64 | 147109 | 13 | 5 | 4 | 436 | 0 | 0.0348 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXNFLTEAMTOTAL | mono | 64 | 8465 | 116 | 111 | 1234 | 220 | 104 | 0.0498 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |
| nested | KXNFLTEAMTOTAL<=KXNFLTOTAL | mono | 63 | 15495 | 0 | 0 | 1 | 2 | 0 | None | 1.0 | NO NET VIOLATION |
| nested | KXNFLTOTAL | mono | 64 | 5806 | 9 | 2 | 138 | 193 | 0 | 0.0081 | 1.0 | NOT DISTINGUISHABLE FROM TIMING/COST |

Largest persistent cell: **NFL TEAMTOTAL ladder** — net 111 of 8,465 observations, persistent 104, max margin 0.0498, median 0.0027, concentrated in 64 games. Placebo net count is 220 (on a paired subset), so the real count is not above timing noise; Holm p = 1.0. It is a watch item, not a finding.

## D4 — Capacity and executability
No cell survived, so no structure qualifies for sizing. The framework, for any future survivor: (1) **leg count** — 2 for MLB/NFL GAME and cross-family edges, 3 for F3/F5/F7 (including TIE), up to the ladder width for within-event ladders; (2) **per-leg depth, SAMPLE ONLY** — `top_of_book_contracts {yes,no}` from the depth rows in the archive, a sparse sample and never a standing constant (CLAUDE.md: depth swings 10–100x intraday); (3) **all-or-nothing fill** — a Dutch book pays only if every leg fills at its quoted ask, so required executable size is the minimum across legs, and a partial fill leaves an unhedged directional position. Capacity is therefore bounded by the thinnest leg at the instant of entry, and cannot be inferred from the archive. For the NFL TEAMTOTAL cluster the legs are 2, depth unmeasured; no capacity claim is made.

## Disclosures
- **Ladder aggregation reading:** an observation is a (set, run) using only rungs with an executable quote (≥2 needed); the margin is the maximum over all pairs i<j. Complementary and cross sets require every leg executable. Max-over-pairs inflates gross counts relative to a single-pair test, and the placebo and sign-flip are computed under the same rule.
- **Intra-run skew is unmeasured.** `run_ts` is a run-level stamp; legs in a run may have been read seconds apart.
- **Placebo and sign-flip are degenerate** (p = 1.0 everywhere): real net counts sit at or below the placebo's wherever it was computed, so the one-sided test has nothing to reject. Not evidence the test is well-powered.
- **H sensitivity is not monotone** with the net count (it substitutes mid ± H for the ask) and sometimes exceeds it; it is a stress, not a lower bound.
- **Cost source:** ask side plus ADR-0016 fee `round(0.07·p·(1−p), 6)` (`paper_trader.py:505`). 44.1's cost surface (GG-325/T-603) had not landed; a re-run on it is owed.
- Session-start Q1–Q7 and the six watchdog questions were not individually answered in this session's output; Step 4 and the protocol outputs were run, Q1–Q7 were not written up. Flagged rather than asserted clean.

## Does multi-leg pricing run looser than single legs, and does any loosening survive crossing every leg?
No. Gross incoherence is common in the complementary cells (e.g. F3 buy-all-YES 678 gross, MLB GAME buy-all-YES 897 gross), but it disappears once every leg is crossed at the ask and fees are paid (5 and 1 net respectively), and in every cell that retained net violations the timing placebo is as large or larger. After the toll, the persistence rule and Holm, the multi-leg structures priced no more loosely than single legs at this 20-minute archive cadence.

## GAPS FOUND -- FOR REGISTRATION BY 44.1 OR WAVE 45
1. **44.1 cost surface not landed** (GG-325/T-603): verdict uses ask + ADR-0016. Re-run `scripts/multileg_coherence.py measure` when it lands.
2. **Archive cadence and skew:** MLB :00/:20/:40, NFL :05/:25/:45; intra-run skew unknown; sub-20-minute incoherence is unobservable here.
3. **GG-322 hazard — stale ID text:** my first claim row (695) still says EXP-032 and ADR-0069; EXP-032 belongs to T-603 (row 694). Row 696 corrects to EXP-033. Readers of 695 alone will mis-attribute.
4. **NFL TEAMTOTAL persistent cluster** (104 persistent obs, 64 games): watch item; more NFL games or tighter cadence needed.
5. **Depth samples sparse** (`top_of_book_contracts`): no capacity estimate possible for any structure.
6. **Bootstrap CIs pre-registered but not implemented.**
7. **GG-149 blind spot:** C4 cannot see same-game exposure across tickers; ADR-0069 (PROPOSED) drafts the mechanism and authorises nothing.
