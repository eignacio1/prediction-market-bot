# Operator Digest — 2026-09-03

**What changed (T-513):**
Finished a previously-approved cleanup: the system now tracks "which historical rule-change applies to which bet" by band *and* sport/market, not band alone. Old records tagged "applies to everything" were accurate when written but would have become misleadingly broad once a second sport showed up. All eleven historical rules were reviewed individually, with written reasoning; nine narrowed to baseball-hits, two deliberately left broad because the underlying change genuinely touched everything at the time. Checked before/after: bet groupings didn't shift — a precision improvement, not a fix to a real error.

**Money impact:** None. No sizing, positions, or bet-eligibility rules changed.

**Decision needed?** None — this implemented a decision you already signed off on (ADR-0054, item b).

**Worry flag:** None new. Two of eleven rules stayed broadly-scoped by design — narrowing wasn't supportable, and policy is scope-wide over risking missed contamination.
