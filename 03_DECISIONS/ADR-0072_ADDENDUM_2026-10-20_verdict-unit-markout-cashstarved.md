# ADR-0072 Addendum — 2026-10-20 — verdict unit, criterion (c) collection, cash-starved days

**Status:** ACCEPTED (operator decisions below). **Amends nothing in the accepted ADR-0072 text** (ADRs are immutable, Hard Rule 3); it fills three gaps the pre-registration left silent, before any score was read. Prior addenda: 2026-10-14, 2026-10-15.
**Decisions logged:** true

## Authorization (quoted from `04_EXECUTION/ACTIVE_QUEUE.md`, "Needs your decision")

> **AUTHORIZATION - ADR-0072 ADDENDUM: THREE PRE-REGISTRATION GAPS (operator, 2026-10-19 ~22:45 PT, asked by the strategic window
> before any score was read).** Verdict unit: "Per book and sport (Recommended)". Criterion (c), the 30-min post-fill markout, never
> collected: "Collect from now; judge (c) forward (Recommended)". Cash-starved days: "Exclude them (Recommended)" (fills before
> 2026-10-16T05:40Z are out of the verdict, reported separately). Covers: a dated ADR-0072 addendum with exactly these three
> decisions; a 30-min markout collector (registered first); the scored read under them. Not covered: seed, share, judged n, the
> placement rule, any switch. Used by 81.1 (add-in 81.1-B).

## The three decisions

1. **Verdict unit = per (book, sport).** Each cell is scored on its own arms; no pooling across sports or books. Judged n (~550 fills/arm) is counted per cell from the labelled box table, not from Wave 76 fill counts.
2. **Criterion (c) is collected from now and judged forward.** `scripts/demo_fill_markout_collector.py` (registered in `RUNTIME_REGISTRY.toml` first) records the held-side two-sided mid at fill+1/5/30 min minus fill price, from demo 1-minute candles. (c) is judged only on fills at/after the collection epoch (`exp_output/FORWARD_TEST/markouts/EPOCH.json`), at the same judged-n rule. Until then a cell whose (a) and (b) hold reads **"(a)/(b) hold, pending (c)" — never ADOPT.**
3. **Cash-starved days are excluded.** Only fills from 2026-10-16T05:40Z count toward the verdict; earlier fills are reported separately, descriptive only.

## Method choices this addendum makes explicit (the pre-registration was silent; flagged, not hidden)

- (a): analytic game-clustered, one-sided 95% lower bound on treatment−control mean (settle − price) on fills.
- (b): fill rate = fills / ok orders submitted, per arm, post-top-up; treatment ≥ 25% of control.
- Eligibility is by order submit time ≥ top-up instant; fills attributed by order.
- Reject rule: one-sided 95% upper bound of the difference < +0.05 at judged n.
- (c) "not worse" fails only if the one-sided 95% upper bound of (treatment−control) 30-min markout is < 0, judged at ≥550 markout-bearing fills per arm; a side with no two-sided quote is missing, never zero.
- The paper book has no treatment/control split, so it is descriptive only.

## Not covered (unchanged)
Seed, share, judged n, placement rule, any switch, any order/stake/kelly change.
