# GG Assertion Retrofit Ledger

**Created:** 2026-08-11 (T-433, ADR-0052)
**Purpose:** Records the `**Assertion:**` mapping (ADR-0052 §2.1–2.2) for governance gaps whose canonical entry already lives in `GOVERNANCE_GAP_LOG_ARCHIVE.md`. That file is moved-to verbatim and never hand-patched for content (see CLAUDE.md, and the archive's own header) — this file is a pointer/annotation layer alongside it, the same relationship ADR-0044's "current-status line + linked history file" pattern established, applied in reverse: instead of relocating dense content out of a live file, this annotates existing immutable content from outside it.

**This file does not change any archived gap's verdict.** GG-149/GG-142/GG-141 remain RESOLVED exactly as archived. This file only records, per ADR-0052, what executable assertion basis (if any) that RESOLVED verdict now rests on going forward.

**Scope:** exactly the three archived gaps named in ADR-0052 §3 — not a blanket retrofit of the other ~111 archived entries. Do not add rows here without a corresponding ADR or task instruction naming the gap.

---

## GG-149 — offsetting/wash-trade positions (161 T4M-PROJ tickers held simultaneous open YES and NO)

**Archive location:** `GOVERNANCE_GAP_LOG_ARCHIVE.md`, `### GG-149`
**Assertion:** `PENDING(T-432, assertion H)`

T-432's baseline run of the offsetting/both-direction-open check (assertion H) against the live ledger found **17/151 T4 violations** — cross-checked against `logic_epoch` and confirmed all 17 predate epoch 12 (the epoch in which GG-149's fix, `scripts/tag_locked_pairs_t4_mlb.py`, landed). This is legacy residue from before the fix, not a live regression — the fix holds going forward. It is recorded `PENDING` rather than `LANDED` under ADR-0052's grammar because T-432's suite itself has not yet formally landed (task brief only as of ADR-0052's drafting); once T-432 lands and is wired into a standing run (not a one-off baseline), this entry should be updated to `LANDED(scripts/assert_ledger_invariants.py::assertion_H)` or equivalent.

**Why this is the strongest of the three retrofits:** GG-149 is the direct positive-control example ADR-0052 opens with — "GG-149 HELD because it is code." The `PENDING` label here reflects only that the *standing* wiring is still in progress, not any doubt about the underlying fix.

---

## GG-142 — C4 `abs(edge)` gate rescuing confidently-wrong bets

**Archive location:** `GOVERNANCE_GAP_LOG_ARCHIVE.md`, `### GG-142`
**Assertion:** `LANDED(tests/test_c4_risk.py::test_negative_directional_edge_rejected)` — plus `test_direction_edge_sign_inconsistency_rejected` and `test_direction_edge_sign_consistent_no_still_approved` (CHECK 4b), and the corrected `test_full_no_approval_flips_probabilities` (previously encoded the bug as expected behavior). All four landed via ADR-0049, `logic_epoch` 9→10.
**Secondary assertion:** `PENDING(T-432)` — fee_net_edge cascade assertion (a data-level standing check across the live ledger, distinct from the unit-level tests above, per the T-432 task brief).

The unit tests are a genuine `LANDED` assertion: they run on every test-suite invocation and would fail loudly if CHECK 3/CHECK 4b regressed to the `abs()` form. They are unit-level (fixture-driven), not a standing check against live ledger data — that's what the secondary fee_net_edge cascade assertion (T-432) adds. Both are recorded because ADR-0052's grammar does not require exactly one assertion per gap; a gap can carry a landed unit-level check and a pending data-level check simultaneously, and both are worth stating rather than picking one.

---

## GG-141 — dead opponent-starting-pitcher matchup columns (100% blank)

**Archive location:** `GOVERNANCE_GAP_LOG_ARCHIVE.md`, `### GG-141`
**Assertion:** `LANDED(scripts/check_feature_column_health.py)`

GG-141's own archived Resolution field states this script was built as its preventive fix, wired directly into `generate_mlb_features.py` immediately after the combined feature DataFrame is built and before the CSV is written. This is the strongest possible confirmation of `LANDED` status short of GG-149's: the assertion did not just get built, it already caught a second, independent instance of the same failure shape on its first live run — that second instance is GG-145 (see the live-log retrofit for GG-145's own `**Assertion:**` field, which cites this same script).

---

## Cross-reference

For the two still-OPEN gaps in the same defect family that were retrofitted directly in `GOVERNANCE_GAP_LOG.md` (not here, since they are not archived), see GG-164 and GG-166's `**Assertion:**` fields — both `PENDING(T-432, assertion A)`.
