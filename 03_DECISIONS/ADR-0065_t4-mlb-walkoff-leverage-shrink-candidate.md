# ADR-0065: T4 MLB Walk-off Leverage Shrink — Candidate Model (PROPOSED, NOT ACCEPTED)

**Status:** PROPOSED — drafted only, per Wave 36 Block 36.2 (T-575 follow-on). Not accepted. Does not supersede any live model. No `logic_epoch` bump has occurred and none is authorized by this document.

**Supersedes:** Nothing yet. If accepted in a future session, this ADR would supersede the incumbent `_compute_ab_remaining` / `p_hits_gte_threshold` pairing (`run_t4_mlb_live.py`) as the live T4 MLB forecasting model, per ADR-0004's frozen-model policy (a live C3 change requires a superseding ADR).

**Author:** Claude (session `20260929T001556Z-t4-game-state-signal`, Wave 36 Block 36.2, Deliverable 5)

**Date:** 2026-09-28

---

## Context

T-569 found the T4 latency thesis NOT SUPPORTED, testing the incumbent model `p_hits_gte_threshold(h_so_far, ab_remaining, ba_l10, threshold)` — a Binomial PMF with `p = ba_l10`, driven by three scalars and an `ab_remaining` estimate computed from innings-left alone, with zero score, outs, base-state, or pitcher awareness. T-575 ranked a live score/leverage signal as the single highest-leverage addition to that exact model, describing the binomial-only incumbent as "close to the weakest plausible model for the latency thesis," and noted the relevant ESPN fields were likely already reachable via the feed T4 already polls.

This block's mandate was explicit: not to re-test the thesis, but to build the model that would make a re-test meaningful. T-569 is not re-run or re-litigated here; it stands at its stated scope.

## Decision (proposed)

Introduce `p_hits_gte_threshold_candidate_v1` (and its two helpers, `_walkoff_leverage_shrink` and `_compute_ab_remaining_candidate_v1`) as a candidate replacement for the incumbent's `ab_remaining` estimation step, narrowly targeting one specific gap: the incumbent has no way to see that a plate appearance can end the game outright in the bottom of the 9th inning or later (the home team taking the lead ends the game immediately), so it systematically overstates `ab_remaining` in that window.

### Functional form

The candidate is the incumbent's unmodified Binomial core (`p_hits_gte_threshold`) fed a different `ab_remaining` input. That input is computed as:

```
naive = _compute_ab_remaining(ab_so_far, inning, batting_slot)          # incumbent, unchanged
shrink = 1.0                                                             # everywhere outside the walk-off window
shrink = 1.0 - (0.15 * (1.0 / (1.0 + |home_score - away_score|)))       # bottom 9th or later only
ab_remaining_candidate = max(0, round(naive * shrink))
```

The shrink applies only in the bottom of the 9th inning or later — the only window in which a single plate appearance can end the game. Outside that window the candidate is byte-identical to the incumbent (proven by test; see Deliverable 2/3 in the results summary). Inside the window, the shrink scales inversely with score differential via `1/(1+|diff|)`: a tied or one-run game shrinks harder than a blowout, on the reasoning that a lopsided score is mechanically walk-off-eligible but empirically far less likely to actually end there on the next plate appearance.

### Stated assumptions (explicit, per the block's own requirement)

1. **Plate-appearance-level walk-off probability is approximated by score differential alone.** Baserunners, outs, and batting order are ignored, even though a runner on third with one out is a materially different walk-off risk than bases empty with two outs at the same score differential. All three fields (base state, outs) were confirmed present in the polled ESPN payload (Deliverable 1) and are already logged (Deliverable 2) — they are simply not yet modeled. A richer candidate could consume them.
2. **`_WALKOFF_BASE_DISCOUNT = 0.15` is a single global constant, deliberately undefended.** It was not fit or validated against any resolved-bet data, because none exists that is both (a) not the forbidden T4M-PROJ cohort and (b) carries the score/inning-half fields this candidate consumes. See "Evidence" below.
3. **The shrink is multiplicative on `ab_remaining`, not a discrete "game over" state.** This is simpler to reason about and test, but slightly overstates continuity risk in the last plate appearances of a blowout — a true walk-off-ended game contributes zero further plate appearances, not a fractionally shrunk number of them.
4. **Only `ab_remaining` is touched.** `ba_l10`, pitcher identity, and pitch count are logged (Deliverable 2) but not consumed by this candidate — left for a future, separately-gated candidate.

### What this candidate does NOT fix

- Pitcher fatigue / bullpen-change risk (pitcher identity and pitch count are logged, not modeled).
- Baserunner- and out-state-aware leverage (both logged, not modeled).
- Batting-order-aware walk-off timing (e.g., whether the current batter is even likely to bat again before the walk-off window closes).
- Any change to the Binomial core's `p = ba_l10` assumption, or to how `h_so_far` enters the model.
- The T-569 finding itself — this ADR does not claim the latency thesis is supported; it proposes a model that would make a future re-test of that thesis meaningful, nothing more.

## Evidence (in place of a harness verdict)

ADR-0042 D2 requires a `DEFENSIBLE_IMPROVEMENT` verdict from `scripts/ab_harness.py` holdout mode before any enhancer activates in the live paper book. That harness run was attempted and could not be validly executed for this candidate, for three independent, converging reasons:

1. **The harness's own default input, `logs/.vps_portfolio_cache_mlb.json`, does not exist** — confirmed both by a live `FileNotFoundError` from running `scripts/run_ab_experiment.py` directly, and by `git log --all` showing the file has never been committed to this repository.
2. **The harness stack (`ab_harness.py` + `run_ab_experiment.py` + `run_exp017b_decomp_mlb.py`) was purpose-built for a different research question.** Per `run_exp017b_decomp_mlb.py`'s own module docstring ("EXP-017B MLB — Edge Decomposition of the Tier-1 T1 MLB Book"), its schema (`model_p`, `mid_price_at_entry`, `kalshi_threshold`, `kalshi_ticker`) and its four registered strategies are T1-MLB book-selection filters. Nothing in the stack has a concept of T4's game-state fields.
3. **No resolved-bet record anywhere — forbidden or not — carries the game-state fields this candidate needs.** The fields were only added to the live pipeline this block (Deliverable 2), are logging-only, not yet deployed pending operator authorization, and per T-577 (2026-09-25, UNRECOVERABLE verdict), the only T4-MLB-specific resolved-bet ledger in existence (`paper_portfolio_mlb_t4.LIVE.20260922.json`) is categorically forbidden as a holdout for this or any purpose, and MLB's 2026 season has already ended, closing this band's accrual window for the year regardless.

This is a genuine data-availability blocker, not a candidate failure and not a workaround of the prohibition on using the forbidden cohort. Per the block's own framing, this is a real result: the governing gate cannot be validly cleared today, so this candidate cannot be activated today, full stop — independent of whatever the candidate's true merit is.

## Activation requirements (unmet, listed for the record)

Before this or any successor candidate can replace the live T4 MLB model:

1. A `DEFENSIBLE_IMPROVEMENT` verdict from `scripts/ab_harness.py` holdout mode, run against a real, non-forbidden, game-state-bearing T4 MLB resolved-bet cohort of adequate size — which does not exist today and requires (a) Deliverable 2's logging fields deployed live (operator authorization, 36.3's lane), (b) weeks of fresh accrual once deployed, and (c) MLB's next season, since 2026's window has closed.
2. Operator signature on this ADR (currently absent — status PROPOSED).
3. A `logic_epoch` bump marking the activation (per the project's epoch-tracking convention).
4. This ADR moved from PROPOSED to ACCEPTED, or superseded by a later ADR with different evidence.

None of these four conditions are met as of this draft. This ADR is submitted for the record and for the operator's future reference — not for action today.

---

*Drafted, not accepted. See `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/WAVE36_BLOCK36-2_RESULTS_t4_game_state_signal.md` for the full block writeup (Deliverables 1-4 in detail).*
