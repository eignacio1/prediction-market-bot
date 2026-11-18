# SESSION_HANDOFF W87.1 — Quant A1 finished (scoring infrastructure, not a factor)

```
vision_pillar: PROOF
gap_measure: scoring paths reconciled with the core; paths re-pointed to the core; D3 (EXP-041 counted, GG-1100)
gap_delta: reconciled 2 -> 9 (0 bugs, 4 definition differences GG-1180..1183); re-pointed 0 -> 3 (fee_k007, nhl edge_net, scoring cluster_bootstrap_ci); helpers absorbed: ladder, coherence, dtmc; D3 1 -> 3
pattern_sweep: GG-1100 pattern (a scorer keyed on filename/status instead of the files' own content) searched in scripts/ and src/; no other instance found. Otherwise n/a
surface_delta: none (no new running component; no runner touched)
```

PRs: #333 (Part A, f15c2a7), #335 (Part B, 749b873). Detail: `12_EXPLORATORY/quant_core_reconcile/results_W87.md`.

**Open:** (1) Box read-back not done: at the time of check the box was at f15c2a7 (Part A only); Part B's deploy had not landed. Next calibration-engine run after deploy should equal the previous numbers (equality tests passed on frozen snapshots). (2) Deferred for time: t4_fill_status bootstrap (keep None-guard + 4-dp rounding), calibration_diagnostics.ece/reliability/brier_murphy, five unexamined scorers (listed in results). (3) scipy is not declared in pyproject (arrives via scikit-learn); quant.ladder needs it. Operator decisions: none.
