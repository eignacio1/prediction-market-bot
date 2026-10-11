# ADR-0072 (DRAFT) — Demo-venue fills: order-placement rule

**Status:** ACCEPTED (operator, 2026-10-10 19:13 PT; switched ON demo-only 2026-10-11, W66.2) · **Switch:** OFF by default (`DEMO_FILL_PLACEMENT_RULE` unset = current behaviour) · **Date:** 2026-10-09 · **Wave:** 63.3
**Note:** number provisional; renumber at merge if ADR-0072 is claimed elsewhere. Nothing in this ADR is built or enabled.

## Design input (Part B evidence)

Source: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W63_3_distance_generator_fill_markouts_results.md`. Read-only demo-venue GETs; game-clustered 95% CIs.

1. **Fills are adversely selected.** Settled win rate of CONFIRMED_FILLED vs never-filled orders: T1 MLB 28.2% vs 50.6%; T4 MLB 24.1% vs 48.7%. Price-adjusted settlement markout (win − price paid): filled −0.39 [−0.49, −0.28] / −0.25 [−0.37, −0.11]; never-filled +0.07 / +0.10.
2. **The filled set is the losers.** Orders are good-till-canceled limits at the model mid. They rest for a median of 5,873 s (T1) / 2,276 s (T4) and fill when the market moves against the held side. Post-fill markouts are negative at 1/5/30 min (T4 ≈ −0.17 at all three, CI excludes 0); markouts from submit are ≈0 — the loss is incurred between submit and fill.
3. **Stale pricing is a second factor.** The ledger mid sits below the venue mid by 0.12 (T1) to 0.16 (T4, filled) on the minority of rows with a two-sided book; limits sit 0.27–0.54 below the ask. A bid that far from the offer fills only when the book collapses toward it.
4. **Immediate fills are not the problem.** T4 fills ≤60 s: win rate 35% (CI wide, n=51), settle-at-fill-price −0.07 [−0.40, +0.15]; resting fills (>60 s): win 19%, −0.33 [−0.41, −0.24].

Interpretation: adverse selection of resting orders, compounded by model-mid prices that lag the venue book. Not a latency or take-vs-make fee effect.

## Candidate rules (to be tested, not adopted)
- **R1 cancel-after-N:** cancel unfilled orders after N s (evidence suggests N ≈ 60 s; immediate fills are the benign subset). Cheapest; removes the stale-resting population.
- **R2 price vs book:** price relative to the observed venue bid/ask rather than the model mid; skip when the book is one-sided or the mid gap exceeds a threshold.
- **R3 take vs make:** insufficient evidence; taker share is 3.5% (T1) / 24% (T4) and the taker subset is small.

Evidence best supports **R1, with R2 as a pre-condition**. This cannot be validated from existing data: it needs a forward test on the demo venue.

## Decision requested (W64.2)

Accept this ADR and the forward-test pre-registration below, so the operator may switch the two OFF-by-default switches ON. **Status stays PROPOSED until he does.** Built and merged in PR #208 (switches OFF; nothing placed, enabled or configured). Demo only, `kelly_fraction` 0, no real money.

### Forward-test pre-registration (written before any treatment data exists)

**Switches.** `DEMO_FILL_PLACEMENT_RULE=book_anchor_cancel` (R1+R2 on the existing demo order path) and `SHADOW_FLAT_STAKE=on` (flat demo stakes on SHADOW cells; requires the first switch). Parameters at registration: cancel after N=60 s, max model-vs-book mid gap 0.05, assignment share 0.5, seed `w64-2`.

**Which books and cells.** (1) T4M-PROJ (`t4_mlb`) and T1 MLB demo orders, as today. (2) SHADOW cells whose logged net-of-fee (k007) edge > 0, one flat ADR-0050 demo order per row. Shadow cells are reported separately and never pooled with (1): they have no prior fill history.

**Assignment.** Each eligible order is hashed (`sha256(seed|position_id)`); the first 50% go to treatment (policy applies), the rest are control (today's behaviour: model-mid GTC limit, no cancel). Deterministic and reproducible from the stored id; the arm is recorded in the order log. The seed and share are frozen for the test; changing either restarts it.

**Primary measures (per arm, per book).** Fill rate; win rate on fills; settle minus price on fills (the 63.3 headline: control baseline −0.25 T4, −0.39 T1); markout after fill at 1/5/30 min (demo 1-minute candles, two-sided mid only). Also reported: skip rate by reason, cancel success rate.

**Judged n, from 63.3's measured variances.** 63.3's T4 settle-minus-price on fills was −0.25 with game-clustered 95% CI [−0.37, −0.11] at n=166 over 66 games, so the clustered SE is about 0.066 against an iid SE of about 0.033 (binary outcome, SD about 0.5): design effect about 4. Smallest effect worth acting on: +0.15 (half-way from −0.25 to 0). One-sided alpha 0.05, power 0.80: n = 2 x 0.25 x (1.645+0.84)^2 / 0.15^2 = about 137 fills per arm iid, **about 550 fills per arm after the design effect**. At 63.3's T4 fill rate (166 of ~4,220 orders, 3.9%) that is about 14,000 control orders per arm, and fewer fills still in the treatment arm. We therefore judge on **fills**, not orders, and state in advance that if 550 control fills are not reachable within 8 weeks the test is declared underpowered, reported descriptively, and not used to accept or reject R1/R2. Until the judged n is reached, no verdict; interim looks are descriptive only.

**Verdict rule (all must hold).** (a) One-sided game-clustered 95% lower bound on (treatment minus control) mean settle-minus-price on fills is above 0. (b) Treatment fill rate is at least 25% of control's (a policy that simply stops trading has not fixed anything). (c) Post-fill markout at 30 min in treatment is not worse than control. If (a) holds but (b) fails, the verdict is "removed fills, not adverse selection" and the rule is not adopted. If the upper bound of the difference is below +0.05 at judged n, the rule is rejected.

**Turn off (the operator, or any session, sets the switch unset) if:** the cancel call fails on more than 10% of attempts in a day (the cancel path is **unverified** against the demo API at merge; the first ON day is its verification); the skip rate exceeds 90% for three days (policy is inert); the order log has a scheduled cancel with no outcome after 15 minutes (the sweep failed); treatment 30-minute markout is worse than control by more than 0.05 with a CI excluding 0; or any order appears on a non-demo host.

**What this test cannot show.** It measures demo-venue fills only, on a thin demo book. It does not say what a live venue would do and it does not touch the commercial-validation gap (GG-004).

## Caveats
Demo book is thin/one-sided: venue-mid coverage is small (T1 n=6, T4 n=13 filled). Never-filled markouts from submit (+0.18 to +0.30) mostly reflect limit-to-book distance, not information, and are not used for the verdict. Never-filled orders are mostly ledger-derived (order GETs 404 for 301 of 551 sampled); ledger-limit vs order-limit matched 1 of 2 checked.
