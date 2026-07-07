# FR-03 Evidence — Calibration Evaluation (Brier + log loss vs null model)

**Requirement:** (a) Brier score computed correctly against held-out outcomes; (b) Log loss computed correctly; (c) Both metrics compared to null model (market-implied probability); (d) Results written to timestamped file with Snapshot ID.

**Populated:** 2026-07-06 (GG-075 remediation).

## Evidence

- **vs. 0.50 null baseline (G4 criterion as originally scoped):** `07_TEST_VALIDATION_EVIDENCE/VALIDATION_REPORTS/G4_VALIDATION_REPORT.md` — G4 CLOSED 2026-05-28. Metric math verified by `tests/test_c3_calibration.py`.
- **vs. real market-implied probability (the commercially meaningful null, GG-004/EXP-017):** `scripts/run_exp017_mlb.py` / `tests/test_t184_exp017_mlb.py`. Current result (re-verified 2026-07-06, T-184): **n=151 unique resolved MLB positions, EV=+$0.1009/bet, win rate 49.7%, total P&L +$15.23, verdict DIRECTIONAL_POSITIVE** — CLAUDE.md/GG-004 describe this as "ADR-0024 Tier 1 (n≥150 single-sport) REACHED." Tier 2 (n≥500 single-sport) not yet met. Full breakdown: `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-004.
- **Direction-split caveat:** YES bets (n=11) are sharply negative-EV and small-sample — a watch item per GG-004, not a stop-work signal.
- **Terminology caveat (surfaced by the GG-074 audit, 2026-07-06):** "Tier 1"/"Tier 2" is informal shorthand introduced in GG-004's own log entries to describe interim progress, not a threshold formally defined by ADR-0024's text. ADR-0024 itself defines one sample-adequacy bar for its G6 checklist item T0-A: "≥500 unique markets + ≥15 distinct opponents, OR ≥2 sports each with n≥150." MLB alone at n=151 is progress toward the "≥2 sports each n≥150" leg (NBA is at n=0, so that leg is not yet satisfied) and is well short of the "≥500 unique markets" leg — the ADR-0024 bar itself has not been met by either path. Do not read "Tier 1 REACHED" as satisfying `08_MODEL_RISK_GOVERNANCE/G6_GATE_CHECKLIST.md`'s T0-A, which remains correctly OPEN/BLOCKING.

## Status

**PARTIALLY MET, upgraded from the 2026-07-02 pass.** The 0.50-null leg has been closed since G4. The real-market-null leg (the criterion's actual intent) is no longer "not yet run" — EXP-017 has run and produced a real, positive, dated result as of 2026-07-06. Whether that result satisfies ADR-0024's formal sample-adequacy bar for G6 is a separate, still-open question (see terminology caveat above) — GG-004 stays OPEN and G6_GATE_CHECKLIST.md's T0-A stays BLOCKING. Do not read this as the full FR-03 criterion being met at commercial strength — it is a real, logged milestone toward it, not the gate itself passing.
