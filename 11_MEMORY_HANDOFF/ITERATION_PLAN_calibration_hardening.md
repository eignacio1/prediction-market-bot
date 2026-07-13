**RETIRED 2026-07-12 (T-348/GG-107).** All workstreams (T-320–T-331) executed and closed — see `DECISION_LOG.md` 2026-07-08/07-11 entries for T-320/T-321 (logic-epoch + backfill), T-322/T-323 (per-band monitor + `n*` power calc, later reframed by APR-0024), T-325/T-326 (property + golden-replay tests), T-328/T-329 (ledger-driven MC + bootstrap CI, extended by T-342), T-330/T-331 (renumbered T-334/T-335 after the GG-107 collision this file itself caused — see below). Moved from repo root to `11_MEMORY_HANDOFF/` as a historical artifact; content below is unchanged and reflects 2026-07-08 planning-time state only — do not treat any status/exit-criterion language below as current.

**Historical note (GG-107):** this file sat untracked and unclaimed in shared `main` for 3+ days after authorship, and its self-reserved T-320–T-331 range collided with a separate session's real T-330/T-331 assignment before anyone noticed (caught only by that session's own Step 0 re-read, not by any structural check). See `GOVERNANCE_GAP_LOG.md` GG-107 for the full account, including a second confirmed instance of the same risk class (GG-111→GG-112 ID collision, 2026-07-12) — the structural fix (extending Step 0c to surface unregistered/unclaimed reservations) remains unbuilt as of this retirement.

---

# Iteration Plan — Calibration & Execution-Path Hardening

**Author:** analytical-copilot session, 2026-07-08
**Status:** PROPOSAL — task IDs assigned **T-320 – T-331** (this session). Basis: at assignment time the
highest T-in-use was T-300 (Window A / context-optimization) and T-280 (Window B / math-rigor), plus the
T-247–261 governance chain; highest GG was GG-102. T-320–331 is a clean block reserved above both active
windows with buffer. **Not yet committed to `SESSION_CLAIMS.md`** — formally reserve before starting by
running `scripts/claim_session.sh` (re-check highest-in-use at that moment per the file's own convention;
do not assume 320–331 are still free if more time has passed). New governance gaps use **GG-103+**.
**Framing (operator directive, 2026-07-08):** sample is inadequate to move strategic calibration
sentiment. Do **not** tune the model on it. Instead, tighten the process so that every bet is produced
under logic that is *repeatable, auditable, testable, and forward-projecting at HIGH confidence*.
Infrastructure maturity is itself the current success — protect it and shift correctness left.

**Governing principle for every item below:** an item is DONE only when it is (a) covered by a test that
would have failed before the fix, (b) reproducible from a clean checkout, and (c) leaves an audit trail.
No item resolves on "looks right."

---

## Why this plan (one paragraph)

The last ~10 days surfaced a run of material, directional bet-logic bugs in the core approval/sizing/
execution path (GG-087 YES-only 41× NO-signal loss; GG-077 fee-sign on 96% of bets; GG-100 monitor
trusting the buggy field; GG-095 Brier ladder auto-firing the kill switch). Governance caught all of them —
**post-hoc**, after they had already contaminated the live paper bet stream. Consequence: the resolved-bet
track record (T1 n=169 negative/inconclusive; T4M-PROJ n≈273–331 positive) is a mix of pre-fix and post-fix
logic, so neither the negative T1 read nor the positive T4 read is yet trustworthy. The strategic question
(is the edge real and which band carries it) is unanswerable until (1) we can isolate bets produced under
current logic, (2) we stop producing new contaminated bets, and (3) our forward projection carries the
sample uncertainty honestly. This plan does those three things and hardens the meta-process around them.

---

## Workstream A — Clean-logic provenance (UNBLOCKS everything strategic)

*Goal: be able to say "N bets resolved under the current, correct logic" per band — the real G6-relevant count.*

### T-320 (A1) — Logic-epoch register
- **Do:** Define a monotonic `LOGIC_EPOCH` integer that increments whenever a fix touches the
  approval / sizing / execution path. Seed the boundaries from history: GG-077, GG-087, GG-100 each closed a
  contaminating bug → each is an epoch boundary. Current epoch = latest.
- **Do:** Persist `logic_epoch` (and the resolving commit SHA) on every new position at `open_position()`.
- **Exit:** every newly opened position carries `logic_epoch` + `approval_commit`; unit test asserts the
  field is populated on all write-path callers (T1/T2/T3/T4M-PROJ).
- **Depends on:** none. **Do this first.**

### T-321 (A2) — Backfill + clean-n reporting
- **Do:** Backfill `logic_epoch` onto historical resolved positions by mapping `game_date`/`entered_at`
  against the known fix-deploy timestamps (idempotent, atomic — mirror `backfill_band_field.py`).
- **Do:** Add a governance-hook line + C8 dashboard panel: **`clean_n`** (bets resolved under current epoch)
  reported *separately* from raw `n`, per band.
- **Exit:** governance hook prints `MLB T1: raw_n=169 clean_n=XX`, `MLB T4M-PROJ: raw_n=NNN clean_n=YY`.
  G6 progress language switches to reference `clean_n`.
- **Depends on:** A1.

---

## Workstream B — Resolve the edge-sign question (the strategic core)

*Goal: on current-epoch bets only, produce an auditable, repeatable per-band verdict — and know how many
more clean bets are needed before that verdict means anything.*

### T-322 (B1) — Per-band anti-predictive + calibration monitor (extends the existing T-255 line)
- **Do:** Run, on `clean_n` only: (i) edge-monotonicity Fisher test (the GG-100 test), (ii) calibration —
  reliability curve + Brier score of `model_p` vs realized outcome. Per band, refreshed on each resolution.
- **Exit:** one command emits `{band → verdict, p, Brier, n}` for the current epoch; wired into the
  weekly monitor cron (GG-099 chain). Verdict on pre-fix epochs is explicitly excluded, not silently mixed.
- **Depends on:** A1/A2.

### T-323 (B2) — Sample-adequacy / power calculation
- **Do:** From observed per-bet EV variance, compute `n*` = clean bets needed to distinguish `edge > 0`
  from `edge = 0` at 95% power, per band. This converts G6's "n≥150/500" heuristic into a real,
  variance-derived target.
- **Exit:** a short memo + a number: "T1 needs ~`n*` clean bets; currently at `clean_n`; ETA at current
  cadence = X weeks." Feeds GG-004.
- **Depends on:** A2.

### T-324 (B3) — T1-vs-T4 divergence memo (analysis, not code)
- **Do:** Quantify why T4M-PROJ (latency) reads positive while T1 (pregame calibration) reads negative/
  anti-predictive. Is it real signal, sizing artifact (T4 is ~$0.47 flat vs T1 proportional), or pre-epoch
  bug residue? Decompose against `clean_n`.
- **Exit:** a decision-log memo with a falsifiable claim about where edge lives. No model change.
- **Depends on:** B1.

---

## Workstream C — Shift correctness LEFT (stop producing contaminated bets)

*Goal: the GG-077/087 bug classes become impossible to ship silently. This is the item that most directly
answers "will cracks get flagged BEFORE they hit the bet stream," which today they do not.*

### T-325 (C1) — Invariant / property tests on the approval path
- **Do:** Encode the exact bug classes as properties: (i) **direction symmetry** — a NO bet on price `p`
  and the mirror YES bet on `1-p` must price/size consistently (kills GG-087); (ii) **fee-sign invariance** —
  `fee_net_edge` computed from the directional frame must equal the direction-aware recompute for both
  YES and NO (kills GG-077); (iii) **edge-frame invariance** — no double-flip between `open_position()` and
  the caller (the GG-077 no-double-flip guarantee).
- **Exit:** property tests (Hypothesis or exhaustive grid) that **fail on the pre-fix commits** and pass now.
- **Depends on:** none (can run parallel to A).

### T-326 (C2) — Golden-replay harness
- **Do:** Freeze a small representative set of game states + market prices with hand-verified expected
  bet decisions (direction, edge, approve/reject, size). CI replays the live approval path against it.
- **Exit:** `tests/golden/` fixture + CI gate; any drift in approval output fails CI with a diff.
- **Depends on:** none.

### T-327 (C3) — Pre-deploy gate on approval-path files
- **Do:** Any diff touching `paper_trader.py` / `run_*_paper_trade.py` / `run_t4_mlb_live.py` / `risk.py`
  must pass C1 + C2 before VPS deploy. Add to the deploy checklist / `deploy.yml`.
- **Exit:** deploy fails closed if an approval-path file changed and the property+golden suites didn't run green.
- **Depends on:** C1, C2.

---

## Workstream D — Forward projection at HIGH confidence

*Goal: the MC stops using hardcoded GG-071 constants and instead carries real, current-epoch inputs WITH
their uncertainty — so "0.01% kill / $1.2M" is never reported as a point estimate again.*

### T-328 (D1) — Ledger-driven MC
- **Do:** Add `mc_forward_projection.py --from-ledger <band>` that reads win-rate, payout multiple, and
  cadence from current-epoch resolved bets rather than module constants. Emit the **{floor / operational /
  ceiling}** band explicitly (zero-edge → ADR-0040 config → observed-edge).
- **Exit:** one command reproduces the A/B/C/E table from live data, no hand-entered constants.
- **Depends on:** A2 (needs clean-epoch inputs).

### T-329 (D2) — Bootstrap confidence on the edge input
- **Do:** Bootstrap-resample the clean-epoch bets to get a CI on per-bet EV; propagate through the MC so
  P(kill) is reported as a **band reflecting sample uncertainty**, not a single number.
- **Exit:** MC output reads e.g. "P(kill 1yr) = 5.4% [90% CI: 0.2% – 41%]" — the CI *is* the honesty.
- **Depends on:** D1, B2.

---

## Workstream E — Meta-process hygiene (protect the thing that's working)

### T-330 (E1) — MEMORY_BANK snapshot consolidation + narrative guard
- **Do:** Collapse the multiple same-day 2026-07-08 snapshots (Terminal 1 / Terminal 2 / S127) into one
  authoritative current-state block; enforce the "one authoritative snapshot, older ones archived" rule.
  This is the recurring GG-082 narrative-conflation mode starting to re-appear.
- **Exit:** single current-state snapshot; a lint/hook that warns when >1 unsuperseded same-day snapshot exists.

### T-331 (E2) — Make worktree isolation the default, not the exception
- **Do:** Document `scripts/new_session_worktree.sh` as the default session launch; add a session-guard
  warning when ≥2 sessions are operating in the shared `main` tree (the GG-101 near-miss condition).
- **Exit:** session-start guard prints an explicit warning + refuses destructive ops when a foreign
  uncommitted state is detected in shared main.

---

## Suggested sequencing (each row ≈ one terminal window)

1. **T-320 (A1)** — logic-epoch on write path *(foundation; nothing strategic is trustworthy without it)*
2. **T-321 (A2)** — backfill + clean-n reporting
3. **T-325 (C1)** — approval-path property tests *(can run in parallel with A)*
4. **T-326 (C2)** — golden-replay harness
5. **T-322 (B1)** — per-band monitor on clean-n
6. **T-323 (B2)** — sample-adequacy `n*`  →  updates the real G6 target
7. **T-327 (C3)** — pre-deploy gate  *(after C1/C2 exist)*
8. **T-328 → T-329 (D1 → D2)** — ledger-driven MC + bootstrap CIs
9. **T-324 (B3)** — T1-vs-T4 divergence memo  *(once clean-n is large enough to read)*
10. **T-330, T-331 (E1, E2)** — hygiene, sprinkle in as low-context filler between the above

**Priority logic:** A unblocks B and D (can't judge or project on a contaminated sample). C is highest-value
*preventive* work and independent of A — it stops the bleeding. B is the strategic payoff but must wait for
A. E is cheap insurance runnable anytime.

---

## Assumptions | Risks | Validation | Confidence

- **Assumptions:** fix-deploy timestamps for GG-077/087/100 are recoverable from git history for A2 backfill
  (high — they're in DECISION_LOG + commit SHAs). Approval-path file list in C3 is complete (verify by grep
  before gating).
- **Key risks:** (1) epoch backfill mis-dates a boundary → clean-n wrong; mitigate by cross-checking against
  commit SHA on-position, not just date. (2) property tests (C1) codify a *current* assumption that is itself
  wrong → mitigate by asserting they fail on the known-bad pre-fix commits. (3) doing B before A tempts a
  premature strategic read on a contaminated sample — sequencing forbids it.
- **Validation checks:** every workstream's exit criterion is a test that fails pre-change; MC changes (D)
  must still reproduce the saved baseline (48.94% 1yr-kill) as a regression anchor.
- **Confidence:** HIGH that this plan makes the *process* auditable/testable/repeatable; the strategic edge
  verdict remains LOW-confidence and deliberately untouched until `clean_n ≥ n*` (B2).
