# SESSION_HANDOFF — T-456 (2026-08-16, worktree session/20260816T010252Z-ledger-market-type)

<!-- session-meta
task_id: T-456
tier: STANDARD
timestamp: 2026-08-16T01:44:00Z
commit: 6173f3f
one_line_summary: T-456: market_type persisted on ledger + power calc regrouped by (market_type, band) cell; T1/T4M-PROJ acceptance test exact match; GG-184 registered
gg_touched: GG-184
adr_touched: none
plan_deliverable_moved: no
-->

**Deliverable:** ADR-0053 delta item 2 — persist `market_type` on ledger, regroup `run_power_calc.py` by (market_type, band) cell. Done, single commit `6173f3f`.

**Backfill decision:** read-time non-destructive derivation (`market_type_for_ticker()`, GG-077 pattern) — never mutates the ledger. Cross-validated 100% agreement vs. stored `band` (T1=466, T2=2, T3=0, T4M-PROJ=2948).

**Write path:** `open_position()` now persists `market_type`. The silent `market_type or MLB_PLAYER_PROP_HITS` default stays (all 7 call sites rely on it), now emits a non-fatal `market_type_defaulted` warning. Registered GG-184 (register-and-stop, Hard Rule 11) rather than making the param required — out of scope.

**Acceptance test:** cell-scoped output for (hits, T1) and (hits, T4M-PROJ) reproduced band-scoped baseline exactly — clean_n, raw_n, n*, mean/stdev, TARGET MET all bit-for-bit identical. Divergence from written prediction: T3 (raw_n=0) has no cell entry (no records → no derivable market_type), unlike `run_all_bands()`'s fixed per-band emission. Reported, not patched — doesn't violate the formal test (named only T1/T4M-PROJ).

**Verification:** `assert_ledger_invariants.py` before/after: zero drift, 677 violations both times, identical per-assertion breakdown. Full pytest before: 2876p/28s/exit0. First after-run surfaced 1 failure (`test_t194...test_emits_c6_warning`) caused directly by this task's own STEP 2 warning addition — fixed in-scope (isolated the assertion to the specific warning event), not registered. Final after-run: 2876p/28s/exit0, matching before exactly.

**What I did not check:** whether any *other* test outside the two full-suite runs implicitly depends on `open_position()` emitting exactly zero warnings when `market_type` is omitted (only the one failure surfaced; did not grep for other silent assumptions). Did not check `t4_mlb_outcome_store.jsonl` cross-path (T-437 scope, pre-existing gap, unrelated to T-456).

**Not touched (per scope fence):** kelly_fraction/sizing/drawdown kill switch, logic_epoch, GG-183/T-454 kill-switch wiring, GG-170, ADR-0053 item 6, box 1.6/1.7, ADR-0053 text, `assert_ledger_invariants.py --strict` promotion.

**Registered:** GG-184 (OPEN, LOW severity).
