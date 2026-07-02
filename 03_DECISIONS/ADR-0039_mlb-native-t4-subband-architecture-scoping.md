# ADR-0039 — MLB-Native T4 Sub-Band Architecture: Scoping (Design Only, No Code Authorized)

**Status:** ACCEPTED (scoped) — DS sign-off received from Earl Ignacio 2026-07-02 (SESSION 109), scoped specifically to implementation authorization for **T4M-PROJ, T4M-ARITH, and T4M-FLOW (including its FLOW-BLOWOUT tree)**. Exact quote: "Yes - you have my sign off. T-4 PROJ / T-4 ARITH / T-4 FLOW + T-4 BLOWOUT can be proceed with." The remaining Tier B roster (T4M-EVENT, T4M-LINEUP, T4M-PITCHER, T4M-BOUNDARY, T4M-STAGED, T4M-CORR, T4M-EXIT) remains scoping-only / not authorized for implementation — this sign-off does not extend to them, including T4M-BOUNDARY despite this ADR having flagged it as an equally cheap next build. Tier A (architecture) is accepted for the whole MLB T4 engine per the two-tier model. **Code authorization ≠ capital authorization**: per Governance Impact below, each of the three authorized sub-bands still requires its own EXP validating its edge hypothesis and a Phase 8 Activation Gate + APR before any paper or live capital deploys.
**Decision makers:** DS (Earl Ignacio), drafted by EL
**Registered by:** T-218 (SESSION 108, 2026-07-02), per operator session-open directive: "T-211 is high priority but requires a new task number and its own ADR (the old target was vacated as NBA-only architecture) — scope MLB-native T4 sub-bands before writing code."
**Drafted:** 2026-07-02 SESSION 108
**Related:** ADR-0029 (NBA T4 sub-band architecture — Tier A frozen, precedent for the two-tier acceptance model used here), ADR-0030 (T4-MICRO carve-out, NBA), ADR-0037 (correction that vacated T-211 as originally scoped), GG-061 (the process gap ADR-0037 registered: verify a target file's actual domain before authorizing code changes to it)
**New governance gaps registered:** GG-066 (MLB has no real-time/sub-poll-interval event feed — blocks any event-driven sub-band)
**Effective:** Immediately for T4M-PROJ/T4M-ARITH/T4M-FLOW(+BLOWOUT) implementation (code only — see capital-authorization caveat above). All other Tier B roster items remain design/scoping only. **No code changes are authorized for any sub-band outside the three named above.** Implementation of the three authorized sub-bands still requires the same per-sub-band gating ADR-0029 applies to NBA (Phase 8 Activation Gate, own EXP, own APR) before capital deploys.

---

## Why This ADR Exists

ADR-0037 vacated T-211 after establishing that ADR-0036 had authorized a flag flip in `t4_execution_engine.py` — the NBA T4 sub-band engine built under ADR-0029 — while describing it in MLB vocabulary. No MLB equivalent of ADR-0029's sub-band architecture exists anywhere in this codebase. `run_t4_mlb_live.py` is a **single flat evaluator**: one Binomial model, one Kelly fraction (`KELLY_T4 = 0.10`), one 45-second poll loop, one decision tree, applied identically regardless of inning, score state, batting slot, or pitcher matchup. This is architecturally the same "monolithic T4" problem ADR-0029 diagnosed for NBA (ADR-0029 §"The Problem with Monolithic T4") — just never fixed for MLB, because MLB T4 was built independently and later (T-190/T-203/T-204, SESSION ~85-94) without inheriting the sub-band redesign.

ADR-0037 was explicit that fixing this requires "a new architecture effort... not a flag flip," "out of scope" of the correction itself, and "would require its own ADR if pursued." This ADR is that effort's **scoping phase only** — per the operator's explicit instruction to scope before writing code, and per GG-061's process fix (verify the target domain before authorizing changes to it — this ADR is built by reading `run_t4_mlb_live.py` directly, not by relabeling NBA text).

**This ADR does not claim MLB T4 sub-bands should copy the NBA roster.** MLB's live-data shape, event granularity, and per-player signal structure are structurally different from NBA's. Sections below establish those differences first, because they change which sub-bands make sense and which don't.

---

## Structural Differences from NBA That Change the Architecture

These four differences were not present in ADR-0029's design context and materially change what an MLB sub-band taxonomy should look like. Each is confirmed by reading `run_t4_mlb_live.py` directly (per GG-061's process fix), not assumed from the NBA precedent.

**1. MLB's C1 data source is poll-only, not event-push.** `run_t4_mlb_live.py` polls the ESPN MLB summary endpoint every `POLL_INTERVAL_S = 45` seconds and diffs `h_so_far`/`ab_so_far` against the previous cycle (`_espn_poll_once_mlb`). There is no play-by-play or live event stream in the current C1 MLB layer — unlike ADR-0029's NBA design, which assumed (and gated behind GG-040) a lineups/play-by-play API with ≤5s detection latency. **Any MLB sub-band whose thesis depends on sub-45s event detection is currently infeasible**, not merely EXP-gated. This is the single most consequential difference and is registered as GG-066 below.

**2. The primary MLB signal is a deterministic state transition, not a probabilistic estimate.** NBA's T4-EVENT reacts to an event (a made shot) that *nudges* a Poisson lambda — the event is evidence, not certainty. MLB's core event — a plate appearance resolving as a hit or an out — **directly and exactly** updates `h_so_far`, the terminal-outcome-defining variable itself. There is no estimation step; `h_so_far >= threshold` is already a hard resolution condition in the existing flat model (`p_t4 = 1.0` special case). This means an MLB event-reaction sub-band, once real-time detection exists (see #1), has a *stronger* and *simpler* edge mechanism than its NBA counterpart: the entire thesis is "did Kalshi re-price this at-bat's outcome before we did," not "how much should this event move a probability estimate."

**3. MLB has an information class with no NBA analogue: pitcher identity.** A batter's true hit probability is materially different against a starter than a reliever, and materially different by platoon split (batter/pitcher handedness). NBA's sub-band taxonomy has no equivalent — there is no NBA concept of "the opposing team swapped out its entire defensive scheme mid-game in a way visible from a single roster event." A pitching change is exactly that for MLB. `ba_l10` (the current model's Binomial success probability) is a season-rolling average blind to who is currently on the mound. This is a distinct, MLB-native information class and is scoped as its own sub-band below.

**4. PA frequency is slot-determined and sparse, not continuous.** NBA minutes accrue continuously across 48 clock-minutes; a player is "in the flow" the whole game. MLB plate appearances are discrete, slot-gated events — a batter gets roughly 3.1–4.2 PAs per game depending on batting order slot (`_AB_BY_SLOT`, already encoded in the current flat model), arriving in bursts once per time through the order (roughly every 20-40 minutes of game time, not continuously). This means MLB sub-bands should be organized around **innings and time-through-the-order**, not a continuous game clock — closer in spirit to NBA's quarter-boundary structure (T4-BOUNDARY) than to its continuous per-minute decay.

---

## Tier A — Architecture (Adopted Unchanged from ADR-0029, Verified Applicable)

The three-layer architecture, staleness arbitration, and immediate-execution principles in ADR-0029 Tier A are **sport-agnostic portfolio-management machinery** — they do not encode NBA-specific assumptions and apply to MLB without modification:

- **Layer 1 (continuous evaluation) → Layer 2 (staleness-arbitrated queue) → Layer 3 (C5 execution + C6 audit).** Unchanged.
- **Principle 1 (Immediate Execution)** and **Principle 2 (Staleness Arbitration)**: unchanged. A bet fires the moment a sub-band's filter approves it; the queue's staleness check (not a scheduled window) governs whether it still executes.
- **Principle 3 (Parallel Evaluation)** and **Principle 4 (Multi-Tree, Bidirectional)**: unchanged. Multiple MLB sub-bands can fire on the same batter/threshold market simultaneously; convergent evidence across mechanistically independent sub-bands is not discounted as correlation.
- **Principle 5 (No Inherited Arbitrary Values)**: unchanged and directly binding on this ADR — every numeric value proposed in Tier B below is explicitly marked provisional pending EXP, exactly as ADR-0029 required for NBA.
- **Principle 6 (T4-CORR Downward-Only)**: unchanged.
- **Kill switch tier structure**: unchanged in *structure* (sub-band budget → T4-band budget → system kill switch). The **SLA value** is not simply inherited — see below.

**One Tier A value requires re-derivation, not adoption: kill switch SLA.** ADR-0029 derived ≤5s for NBA from continuous per-second event density ("continuous evaluation potentially firing multiple signals per second"). MLB's current architecture polls every 45s and, per difference #4 above, PA arrival is naturally sparse. A ≤5s SLA may be unnecessarily strict (over-engineering relative to MLB's actual event cadence) or may be exactly wrong in the other direction once a real-time feed exists (a single at-bat can move `p_t4` from 0.3 to 1.0 instantly — a fast-moving certainty event, unlike NBA's gradual posterior drift). **This is EXP-required, not assumed from NBA.** Provisionally: retain the existing file-based kill switch (`t4_mlb_kill_switch.flag`, halts within one 45s cycle) as the operative SLA until a sub-band with a materially faster edge-decay profile is scoped and activated — at which point that sub-band's Activation Gate must independently justify its required SLA.

---

## Tier B — Provisional MLB-Native Sub-Band Roster

Per Principle 5, every item below is a design hypothesis, not a frozen value. Nothing here is authorized for capital deployment. Each sub-band requires its own EXP and Phase 8 Activation Gate before code is written, exactly as ADR-0029 required for each NBA sub-band.

### T4M-PROJ — Continuous Binomial Projection (existing flat model, reclassified as the architectural spine)

**Information class:** Accumulated `h_so_far`/`ab_so_far` from 45s ESPN polling → Binomial survival recompute against `ba_l10`-derived success probability and slot-based `ab_remaining`. **This is the current `run_t4_mlb_live.py` model, unchanged in substance** — this ADR reclassifies it as one sub-band among several rather than the whole of T4, mirroring how ADR-0029 reclassified monolithic NBA T4 into T4-PROJ as "the architectural spine."

**Natural update frequency:** Every 45s poll cycle (current `POLL_INTERVAL_S`), or on any detected `h_so_far`/`ab_so_far` change.

**Status:** Already built and running. No new work required to stand this sub-band up — it is the baseline every other sub-band below is scoped as an *addition* to.

---

### T4M-EVENT — Discrete At-Bat Outcome Reaction

**Information class:** Per difference #2 above, a single resolved plate appearance for a tracked batter (hit / out / walk / HBP) is a deterministic update to `h_so_far`, not a probabilistic nudge. The edge thesis: Kalshi's price lags the at-bat outcome, not just the game state.

**Natural update frequency:** Per plate appearance — **blocked pending GG-066.** The current 45s poll cycle already captures this update indirectly (T4M-PROJ re-fires on the next cycle after `h_so_far` changes), so T4M-EVENT's entire value proposition is closing the gap between "at-bat resolves" and "next 45s poll" — a real-time or near-real-time (target: ≤10s) MLB event feed is a hard prerequisite, not an optimization.

**Critical pre-activation EXP (same discipline as NBA's ADR-0029 T4-EVENT):** Measure actual Kalshi KXMLBHIT re-pricing latency after a hit is publicly known (ESPN gamecast update or equivalent), across N ≥ 50 at-bats. If mean re-pricing latency is already faster than a feasible MLB polling cadence, the sub-band has no exploitable window and should not be built.

**Kelly fraction, materiality gate:** EXP-required. Not proposed here (Principle 5).

---

### T4M-PITCHER — Pitching Change Reaction

**Information class:** Per difference #3 above — an MLB-unique information class with no NBA equivalent. A starter-to-reliever transition (or a platoon-relevant reliever-to-reliever transition) changes the true success probability underlying every open batter market for the team currently at bat, independent of any change to `h_so_far` itself.

**Natural update frequency:** Per pitching change detected (typically 3-6 per game per team — far sparser than T4M-EVENT, closer to NBA's T4-LINEUP cadence).

**Distinction from T4M-LINEUP below:** T4M-PITCHER concerns the *opposing* pitcher changing (affects the probability model for the batting team's whole lineup simultaneously — a portfolio-dimension event, like NBA's T4-LINEUP). T4M-LINEUP concerns the *batting* team's own lineup changing (pinch hitters, defensive substitutions altering who bats).

**Data prerequisite:** Pitcher-identity and handedness data per plate appearance is not currently in the C1 MLB feature set (`ba_l10` is pitcher-blind). This requires a new C1/C2 data source (likely MLB Stats API `hydrate=probablePitcher,pitchHand` or live boxscore pitcher-of-record) before this sub-band's model can be built at all — this is a data-availability gap, separate from and in addition to GG-066.

**Model class, Kelly fraction:** Not proposed here. Requires establishing a platoon-split/pitcher-tier adjustment to the Binomial success probability before any sizing question is meaningful — a modeling research task, not just an EXP.

---

### T4M-LINEUP — Batting-Team Lineup Change

**Information class:** Pinch hitters, defensive substitutions that change who occupies a batting slot, or (rare) lineup-card corrections. Affects the specific batter markets for the players entering/exiting, not the whole lineup (contrast with T4M-PITCHER).

**Natural update frequency:** Per substitution detected — blocked pending GG-066 for the same reason as T4M-EVENT (ESPN poll-only detection means this is already partially captured by the next T4M-PROJ cycle; the sub-band's value is closing that latency gap).

**Kelly fraction, exposure constraint:** EXP-required.

---

### T4M-FLOW — Accumulated Game-State Pattern

**Information class:** Sustained multi-inning patterns: blowout-driven lineup shuffling (bench players entering late in lopsided games), extra-innings PA-count inflation (more ABs than the 9-inning `AB_PER_GAME_DEFAULT`/`_AB_BY_SLOT` baseline assumes), weather-delay effects on remaining ABs.

**Natural update frequency:** Per inning completion, re-evaluated against rolling game state.

**Note — extra innings is a real, currently-unhandled gap in the flat model:** `_AB_BY_SLOT` is a 9-inning baseline. A game entering extra innings systematically understates `ab_remaining` for the existing T4M-PROJ model today, independent of any new sub-band — this is worth flagging as a candidate near-term fix to the *existing* flat model regardless of whether T4M-FLOW is built, and should be raised as its own low-effort task if not already tracked.

**Kelly fraction:** EXP-required.

---

### T4M-BOUNDARY — Half-Inning / Time-Through-Order Structural Reset

**Information class:** Per difference #4 — MLB's natural structural checkpoint is not a clock boundary but "this team's turn at bat has ended." At each half-inning transition, re-evaluate all open T4M positions for the team that just finished batting (their next PA is a full time-through-the-order away) and re-scan for new entries as the other team comes to bat.

**Natural update frequency:** Per half-inning transition (18+ per 9-inning game — much more frequent than NBA's 4 quarter boundaries, reflecting MLB's more granular structural rhythm).

**Model class:** Full T4M-PROJ re-run at each half-inning boundary. Primarily an EXIT/reassessment sub-band, secondary new-entry scan — same shape as NBA's T4-BOUNDARY.

---

### T4M-ARITH — Threshold-Approaching Arithmetic Near-Certainty

**Information class:** The existing flat model already contains a degenerate form of this (`h_so_far >= threshold → p_t4 = 1.0`; `h_needed > ab_remaining → p_t4 = 0.0`). This sub-band formalizes the *near*-certain band between those hard boundaries — e.g., 1 hit needed with 1 AB remaining — where Binomial variance has contracted enough that a distinct (likely higher) Kelly fraction is justified, mirroring NBA's T4-ARITH distinction from T4-PROJ.

**Natural update frequency:** Per plate appearance for batters within an arithmetic entry window (same GG-066 dependency as T4M-EVENT for real-time firing; degrades gracefully to next-45s-poll firing without it, same as T4M-PROJ today).

**Kelly fraction:** EXP-required. Subject to the same tail-calibration caution ADR-0029 raised for NBA's T4-ARITH/T4-PROJ NEAR-CERTAIN regime — near-certainty is exactly where an uncalibrated model is most dangerous to oversize.

---

### T4M-STAGED — Pre-Game Conditional Fill

**Information class:** Identical mechanism to NBA's T4-STAGED — a T1/T3-approved signal with a pre-set resting limit order at a trigger price. Sport-agnostic execution mechanism; no MLB-specific redesign needed.

**Kelly fraction, noise buffer:** Inherits from T1/T3 MLB values, same logic as NBA's T4-STAGED inheriting T3.

---

### T4M-CORR — Cross-Market Correlation Overlay (Portfolio Sub-Band)

**What it does:** Same mechanism as NBA's T4-CORR. MLB-specific correlation cases: the same batter's 1+-hit and 2+-hit threshold markets move together on a single AB outcome (near-perfect correlation, same-player-different-threshold case); teammates during the same half-inning share game-state correlation (e.g., all trailing-team batters in a blowout).

---

### T4M-EXIT — Active Position Management (Portfolio Sub-Band)

**What it does:** Same mechanism as NBA's T4-EXIT (reversal check, noise-buffer check, time-based floor), with the time-based floor expressed in innings/PAs-remaining rather than clock minutes.

---

## Governance Impact

**GG-066 (new)** — registered below. MLB C1 has no real-time/sub-poll-interval event feed; this blocks T4M-EVENT, T4M-LINEUP, and (for real-time firing) T4M-ARITH from being anything more than "the same as T4M-PROJ, one poll cycle later" until resolved. This is the load-bearing infrastructure gap for most of this roster's value.

**No code is authorized by this ADR.** T-218 is scoping-only, matching the operator's explicit instruction. Building any sub-band above requires: (1) resolving its stated data prerequisite where one exists (GG-066 for event-driven bands; a new C1 pitcher-identity source for T4M-PITCHER), (2) an EXP per sub-band validating its edge-window hypothesis, (3) a Phase 8 Activation Gate and its own APR before capital (paper or otherwise) deploys — the same two-tier discipline ADR-0029 established for NBA.

**Recommended build sequence** (informal, not binding — DS to confirm at implementation time): T4M-BOUNDARY and T4M-ARITH require no new data source and no GG-066 resolution — they are the cheapest next build against the existing 45s-poll architecture. T4M-EVENT, T4M-LINEUP, and T4M-PITCHER each require infrastructure work (a real-time feed or a new C1 data source) before an EXP is even possible.

---

## G6 Implications

None. This ADR authorizes no capital deployment and no code change. It exists to satisfy the operator's scoping requirement before any MLB T4 sub-band implementation task is opened, and to close out GG-061's process fix (verify target domain before authorizing changes) applied prospectively rather than retrospectively.

---

## DS Sign-Off

**Received — scoped.** 2026-07-02, SESSION 109. Earl Ignacio, in response to this ADR being surfaced with its full Tier B roster and caveats (GG-066 blocking 3/10 sub-bands, T4M-PITCHER's missing data source, the extra-innings `_AB_BY_SLOT` bug) at next-session open: **"Yes - you have my sign off. T-4 PROJ / T-4 ARITH / T-4 FLOW + T-4 BLOWOUT can be proceed with."**

This is read as a deliberately scoped authorization, not blanket acceptance of the full Tier B roster — it names three sub-bands specifically and omits T4M-BOUNDARY, which this ADR had flagged as an equally cheap next build alongside T4M-ARITH. That omission is respected: T4M-BOUNDARY is NOT authorized for implementation under this sign-off. Any future extension to additional sub-bands requires its own explicit sign-off, not inference from this one.

Per Governance Impact below, this sign-off authorizes writing code for T4M-PROJ (reclassification/labeling of the existing flat model), T4M-ARITH, and T4M-FLOW(+BLOWOUT) — Phase-8-blocked by default per the ADR-0029 pattern (`_assert_sub_band_blocked()` guard). It does not authorize any paper or live capital deployment for any of the three; that requires each sub-band's own EXP + Activation Gate + APR, unchanged from this ADR's original Governance Impact section.
