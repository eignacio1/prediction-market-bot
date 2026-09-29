# Wave 36 Block 36.2 Results — T4 MLB Game-State/Leverage Signal

Task: `04_EXECUTION/ACTIVE_QUEUE.md` lines 177-239, "36.2 — GIVE T4 EYES: SCORE AND LEVERAGE STATE — STANDARD." Context: T-569 found the T4 latency thesis NOT SUPPORTED against the incumbent Binomial model (three scalars, zero game-state awareness); T-575 ranked a live score/leverage signal as the single highest-leverage addition to that model. Mandate: build the model that would make a re-test meaningful — not re-test the thesis itself. T-569 is not re-litigated here.

Branch: `session/20260929T001556Z-t4-game-state-signal`, worktree `PM-worktrees/20260929T001556Z-t4-game-state-signal`, based on `origin/main` tip `2510c46`.

---

## Deliverable 1 — Is the data already in hand?

T-575's claim ("likely reachable via the same ESPN feed T4 already polls") was verified by direct inspection of the ESPN payload structure T4's live poll consumes.

| Field | Status |
|---|---|
| Current score, both teams | Present in payload; **discarded** (not parsed into `MLBLiveBatterState` prior to this block) |
| Inning + half | Present; **discarded** |
| Outs | Present; **discarded** |
| Base state (1st/2nd/3rd) | Present; **discarded** |
| Pitcher identity | Present; **discarded** |
| Pitch count | Present; **discarded** |

All six fields confirmed present in the already-polled payload. The Deliverable 1 STOP condition ("if score state is NOT in the payload, stop and report what fetching it would require") did **not** trigger. No new data source, subscription, or price-capture-window change was needed or added.

## Deliverable 2 — Extend the state object (no model change)

`MLBLiveBatterState` was extended with 10 new default-valued fields (`home_score`, `away_score`, `inning_half`, `outs`, `on_first`, `on_second`, `on_third`, `current_pitcher_id`, `current_pitcher_name`, `pitcher_pitch_count`), populated by a new defensive extraction function `_extract_espn_game_state()` and written into the cycle-log row.

**Proof `p_t4` is unchanged:** `_extract_espn_game_state()` is covered by tests proving (a) graceful fallback to the declared defaults when keys are missing from the payload, and (b) correct extraction on realistic real-shaped input. Separately, `p_hits_gte_threshold` — the live forecasting function — takes no game-state argument at all; it is structurally impossible for these new fields to change its output, and no call site was altered to pass them in. This was the design choice, not incidental: the new fields are logged, not modeled, in this deliverable. Full existing test suite passed with the extension in place (no regressions).

Committed `dacb89a`, pushed.

## Deliverable 3 — Enriched candidate, offline only

`p_hits_gte_threshold_candidate_v1` (plus helpers `_walkoff_leverage_shrink`, `_compute_ab_remaining_candidate_v1`) was added immediately after the incumbent `p_hits_gte_threshold`, gated behind an explicit "NOT LIVE" banner comment.

**Functional form:** the incumbent's `_compute_ab_remaining` projects remaining plate appearances from innings-left alone and cannot see that a plate appearance in the bottom of the 9th or later can end the game outright (home team takes the lead → game over, no further PAs that inning). The candidate multiplies the incumbent's `ab_remaining` by a shrink factor — 1.0 everywhere outside that window, dipping by up to a flat 0.15 inside it, scaled down as the score gap widens (`1/(1+|score_diff|)`) so a one-run game shrinks harder than a blowout. The Binomial core is untouched; only the `ab_remaining` input changes.

**Stated assumptions:** (1) plate-appearance-level walk-off probability is approximated by score differential alone, ignoring baserunners/outs/batting order (all logged per D2, none modeled here); (2) `_WALKOFF_BASE_DISCOUNT = 0.15` is a single global constant, deliberately undefended — D4 found no non-forbidden data to fit it against; (3) the shrink is multiplicative rather than a discrete "game over" state, slightly overstating continuity risk in the very last plate appearances of a blowout.

**Proof of isolation:** a dedicated test (`test_candidate_not_referenced_by_run_cycle_or_any_live_path`) scans `_run_cycle`'s own source via `inspect.getsource` and asserts none of the three new candidate names appear in it. Two further tests prove the candidate is byte-identical to the incumbent outside the walk-off window (at both the `ab_remaining` and end-to-end `p_t4` level); three more cover window gating, leverage weighting (tie shrinks more than blowout), and case-insensitivity on `inning_half`. Full scoped suite: 217 passed (209 prior + 8 new), zero regressions.

Committed `11552dc`, pushed.

## Deliverable 4 — A/B harness (the governing gate)

ADR-0042 D2 requires a `DEFENSIBLE_IMPROVEMENT` verdict from `scripts/ab_harness.py` holdout mode before any enhancer can activate live. The harness was run and could not be validly executed for this candidate, for three independent, converging, and fully evidenced reasons — this is a genuine data-availability blocker, not a candidate failure and not a route around the prohibition on the forbidden T4M-PROJ cohort.

**1. The harness's own default input does not exist.** `scripts/run_ab_experiment.py`'s `DEFAULT_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")`. Running it directly produced:

```
Traceback (most recent call last):
  File ".../scripts/run_ab_experiment.py", line 158, in <module>
    raise SystemExit(main())
  File ".../scripts/run_ab_experiment.py", line 119, in main
    recs = H.load(args.portfolio)
  File ".../scripts/ab_harness.py", line 71, in load
    recs = d17b.load_records(portfolio)
  File ".../scripts/run_exp017b_decomp_mlb.py", line 91, in load_records
    data = json.loads(path.read_text())
  ...
FileNotFoundError: [Errno 2] No such file or directory: 'logs/.vps_portfolio_cache_mlb.json'
```

`git log --all --oneline -- "logs/.vps_portfolio_cache_mlb.json"` returns nothing — this file has never been committed in this repository's history, on any branch.

**2. The harness stack was purpose-built for a different research question.** `scripts/run_exp017b_decomp_mlb.py`'s own module docstring: "EXP-017B MLB — Edge Decomposition of the Tier-1 T1 MLB Book." Its `load_records()` schema (`model_p`, `mid_price_at_entry`, `kalshi_threshold`, `kalshi_ticker`) and its four registered strategies (`quarantine_YES`, `min_edge_0.10`, `YESquar+min_edge_0.03`, `platt_recal_edge>0`) are T1-MLB book-selection/recalibration filters. Nothing in the stack has a schema concept of T4's game-state fields.

**3. No resolved-bet record anywhere carries the fields this candidate needs.** `find . -iname "*paper_portfolio*"` locates exactly one T4-MLB-specific portfolio file in the entire repo: `exp_output/T577_cohort_salvage/paper_portfolio_mlb_t4.LIVE.20260922.json` — the cohort this task explicitly forbids using "as a holdout for anything" (T-577, UNRECOVERABLE verdict, 2026-09-25). Even setting that prohibition aside: this block's D2 game-state fields were only added to the live pipeline this session, are logging-only, not yet deployed (pending 36.3's operator authorization), and would need weeks of fresh accrual post-deployment to produce a valid holdout — and per T-577, MLB's 2026 regular season has already ended (today is 2026-09-28), closing T4M-PROJ's accrual window for the year regardless of any fix timeline.

**Verdict: the governing gate cannot be validly run for this candidate today.** Per the task's own sanctioned framing — "If it does not clear, say so plainly; a candidate that fails its gate is a real result and the block succeeded" — this is reported as the deliverable's honest, evidenced outcome. No synthetic or fabricated historical dataset was constructed to work around this; no forbidden-cohort data was used in any capacity; T-569 was not re-run or re-litigated.

## Deliverable 5 — ADR draft (not accepted)

`03_DECISIONS/ADR-0065_t4-mlb-walkoff-leverage-shrink-candidate.md` — drafted, status PROPOSED. Documents the candidate's functional form, stated assumptions, what it does not fix (pitcher fatigue, baserunner/out-state leverage, batting-order-aware timing), the Deliverable 4 evidence in place of a harness verdict, and states explicitly that activation requires the operator's signature and a `logic_epoch` bump — neither of which this document grants.

**ADR numbering note:** `ADR-0064` was found already claimed by the concurrent T-578 session (`8dc2854`, "T-578: ADR-0064 draft + results summary for park_factor_hits repair" — an unrelated feature audit, sibling Wave 36 work). Verified `ADR-0065` free via `git log --all`, `origin/main`'s tree, and the local worktree before claiming it (GG-256 compliance).

---

## Gap candidates for the record (NOT registered — 36.3 owns GOVERNANCE_GAP_LOG.md/DECISION_LOG.md per this block's explicit scope fence; register-and-stop per Hard Rule 11)

- **Stale test-mock batting-event label.** A test mock in this codebase uses `"SO"` for a strikeout outcome where the real ESPN payload uses `"K"` — noticed incidentally while inspecting payload shape for Deliverable 1. Not fixed in-session (out of scope); flagged here for 36.3 or a future session to register and assess blast radius.
- **T-577's own flagged items, cited for context only (already flagged by T-577, not newly found here):** the CONFIRMED-CANCELED tier's 100% single-date (2026-09-22) concentration, and the UNCONFIRMED-CLEAN tier's bias-screen failure on `mid_price_at_entry`/`size_usd` specifically. Both are why no salvage path was available for Deliverable 4's evidence — cited for traceability, not as a new registration.

---

## Summary for REPORT BACK

- **ESPN payload field inventory:** all 6 fields (score both teams, inning/half, outs, base state, pitcher identity, pitch count) present in the already-polled payload; all previously discarded; none absent. STOP condition did not trigger.
- **`p_t4` unchanged after D2:** proven — new fields are logged only, no live call site passes them to `p_hits_gte_threshold`, full test suite green.
- **Candidate functional form:** multiplicative walk-off-window shrink on `ab_remaining`, leverage-weighted by score differential; Binomial core untouched; stated assumptions documented above and in the candidate's docstring.
- **A/B harness verdict:** cannot be validly run today — no non-forbidden, game-state-bearing T4 resolved-bet cohort exists; harness's own default input file has never existed in this repo; harness stack is schema-built for T1 MLB, not T4. Reported per the task's own sanctioned framing as a real result.
- **ADR draft:** `03_DECISIONS/ADR-0065_t4-mlb-walkoff-leverage-shrink-candidate.md`, status PROPOSED, not accepted.

— Wave 36 Block 36.2, session `20260929T001556Z-t4-game-state-signal`, 2026-09-28.
