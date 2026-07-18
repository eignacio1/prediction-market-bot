# Next Strategy Window — Task List

**Prepared:** 2026-07-17, end of a 2-day governance/efficiency window (ADR-0044 through the 5-terminal gap burn-down). Handoff for whichever Cowork window picks this up next.

**Read this first:** everything below was true as of 2026-07-17. Re-verify before acting — do not treat this file as current ground truth on its own. Pull fresh status on GOVERNANCE_GAP_LOG.md/DECISION_LOG.md for anything you're about to act on. This file is a map of where to look, not a substitute for looking.

---

## 0. Orientation (do this first)

Run an abbreviated session-start check: confirm repo is clean, `main` up to date, no dangling branches/worktrees from the last window. Re-pull the true OPEN gap count fresh rather than trusting any number in this file.

---

## 1. TOP PRIORITY — the GG-105 / APR-0025 / EXP-T4-01 cluster

This is the central open question on the active book right now, and it got materially reinforced this window, not resolved.

- **GG-105** (OPEN): T4M-PROJ's own computed edge is anti-predictive — win rate declines as stated confidence rises. Temperature scaling was tested this window and explicitly ruled out (makes the aggregate calibration look better while making the tercile pattern *worse*, Fisher p goes 0.0212→0.0000 as T rises).
- **APR-0025** (PROPOSED, awaiting your sign-off): empirical-Bayes shrinkage of `ba_l10`. The only tested remediation candidate that moves both the Fisher p-value and the tercile win-rate gap in the correct direction. This is the live decision that unblocks real progress here.
- **EXP-T4-01 was built and run for the first time this window** (previously never run cleanly — GG-050's overcounting bug had contaminated every prior attempt). Result on raw_n=910: DIRECTIONAL_POSITIVE headline (EV=+$0.0294/bet), but its own edge-monotonicity guard independently found the same anti-predictive tercile pattern as GG-105 (Fisher p=0.028) — a second, different analysis method landing on the same shape. This run sits on a contaminated cohort (clean_n=0 due to an epoch-cascade reset from an unrelated T2 fix landing hours earlier) — a first look, not a governance-grade verdict.
- **Open decision, not yet resolved by anyone:** T4M-PROJ crossed the legacy Tier-2 floor (raw_n≥500) but APR-0024's `clean_n`-based standard currently can't be evaluated (clean_n=0, needs to re-accumulate under epoch 6). Do you want EXP-T4-01 re-run against `raw_n` now under the legacy framework, or held until `clean_n` re-accumulates for an APR-0024-consistent verdict? This is registered in GG-046 but not decided.

**Recommended first move in the next window:** review APR-0025 and this EXP-T4-01 finding together — they're now the same conversation, not two separate ones.

---

## 2. Other decisions ready for your sign-off

Found while compiling this list — some predate this window, worth a "still needed?" pass:

- `APR-0027` — NBA drawdown reactivation policy. Low time pressure (~2 months of runway before the reactivation window), but a quick, easy decision to clear.
- `APR-0029` — GG-045 Kalshi market-depth capital ceiling. New this window — real order-book depth data was collected and a capital-ceiling mechanism proposed. Not urgent (current bankroll well under any plausible ceiling) but worth a read.
- `ADR-0042`, `APR-0022` — older pending items, not touched this window. Worth a quick check on whether they're still relevant before assuming action is owed on them.

---

## 3. Real scoped builds remaining (no decision needed to start)

- **GG-059** items (3)-(4): a C8 data-quality dashboard view plus one more item. Correctly *not* force-closed during the easy-sweep pass — assessed as genuine build work, not a quick fix. Ready to hand to a dedicated terminal.
- **GG-091** (mypy --strict remediation): partial progress made (one category triaged, one real bug found and fixed). Real remaining count needs a fresh `mypy --strict` run to re-measure — the original 365/57 baseline is now stale. Low urgency, no capital/gate risk, good filler work for a terminal with nothing else queued.

---

## 4. Scoping conversations needed before any build (not ready to dispatch)

These are big enough that they need your explicit direction on scope before anyone starts building — not a blanket-approval item.

- **GG-066** — MLB real-time/sub-poll-interval event feed. Tier B under ADR-0039; explicitly requires fresh DS sign-off scoped to the specific sub-band before implementation.
- **GG-094** — MLB qualitative/PRF-analogue feature layer. A from-scratch project (taxonomy design, player classification, its own ADR). This is the MLB-side equivalent of the "large institutional build" category you're already planning for NBA.

---

## 5. NBA arm — batched, deliberately untouched

8 gaps (GG-007, 027, 037, 038, 039, 040, 041, 056) parked as one group per your standing instruction — no individual triage, tackled together when NBA's institutional build starts. `APR-0027` (item 2 above) is the one exception worth clearing early since it's cheap and already drafted.

---

## 6. Passive / self-resolving — glance only, no action needed

- **GG-125** (renumbered from GG-124): all four MLB bands read clean_n=0 simultaneously due to the same epoch cascade discussed in section 1. Should self-correct as new bets resolve under epoch 6. Worth a glance if still zero by ~2026-07-23; not urgent before then.
- **GG-078, GG-098**: pre-registered monitors with their own re-check triggers (a data threshold, not a task). No action until those thresholds fire on their own.

---

## 7. Infra, deferred at your request

- VPS dedicated SSH keypair + separate secrets folder (kept outside the git repo) — you said "later." GitHub connector is already authorized, no action needed there.

---

## 8. The thing you actually said you want to do

You mentioned wanting to return to math/edge-focus building once scale/fidelity feels comfortable. Worth naming directly: **item 1 above (APR-0025 / GG-105 / EXP-T4-01) already is that work** — it's the live, central edge-integrity question for the project's highest-volume active band. Clearing that decision may be the natural bridge from clean-up mode back into edge-focus mode, rather than two separate phases.
