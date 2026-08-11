# T-432 Handoff — BLOCK B invariant suite (parked, low tokens)

**Branch:** `session/20260811T043059Z-invariant-suite`
**Worktree:** `/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260811T043059Z-invariant-suite`
**Last commit:** `4b7ce4a` — `scripts/assert_ledger_invariants.py` created (Task 1 done, uncommitted-work-free).

## Done
- All 9 core + 6 extend assertion formulas empirically verified against live portfolio caches (see prior session summary for full baseline table — A-H + I-N, all field names/formulas confirmed).
- `scripts/assert_ledger_invariants.py` written: loads `.vps_portfolio_cache_mlb.json` / `_t4.json` / `t4_mlb_outcome_store.jsonl` from `logs/` (gitignored — must be `cp`'d or `scp`'d in before running), gracefully reports SOURCE_UNAVAILABLE if absent, never crashes into a gate failure, exit 0 always unless `--strict` (unwired, off by default). JSONL report to `logs/ledger_invariant_report.jsonl` + stderr human summary. Cross-path agreement (Task 2) implemented inline as `cross_path_agreement()`, per-band-per-epoch, reports raw rates (no zero-assumption).
- **NOT YET RUN END-TO-END** — script has not been executed against real data in this worktree (source files were in place from prior segment's `cp`; verify they're still present before running, or wc -l is fine).

## Still pending (in order)
1. **Run the script**, confirm it executes cleanly and totals roughly match the manually-verified baselines from the prior segment's table (A: 459/2516 T4M-PROJ overall, 438/627 epoch-12; G/C/D clean once band/presence-scoped; H clean; player-token 1 anomaly).
2. **Write `tests/test_assert_ledger_invariants.py`** — follow `tests/test_band_monitor.py` conventions (sys.path boilerplate for `scripts/`+`src/`, fixture files under `tests/fixtures/`, use `clean_epoch_floor_for_band`/`is_clean_for_band` not hardcoded epochs). Cover at minimum: presence-guard behavior (missing field ≠ violation), band-scoped G (T1 vs T4M-PROJ vs NO_FORMULA band), SOURCE_UNAVAILABLE graceful handling, `--strict` exit-code behavior (0 default, 1 only with `--strict` + violations present).
3. **Task 3 wiring** — same commit: add a call to `assert_ledger_invariants.py` (no `--strict`) into `.claude/hooks/governance_scan.sh` that prints its stderr summary but never touches the hook's own exit code; add Q7 to `CLAUDE.md`'s "ARE WE COMPROMISED?" section: "Field integrity: does the data mean what the label says?" pointing at this script.
4. **Task 4** — write the `--strict` promotion criterion into a deliverable doc (e.g. header docstring already has design rationale; add a "Promotion criteria" section: N consecutive clean alarm-only runs, cadence, acceptable false-positive rate — operator has not specified numbers, propose reasonable defaults e.g. 14 consecutive daily clean runs with 0 false positives before considering `--strict` promotion, explicitly flag as a proposal not a decision).
5. **Commit + push** within scope fence (`scripts/`, `tests/`, `.claude/`, one doc — no `src/`, no touching `run_t4_mlb_live.py`/`run_resolve_mlb.py`).
6. **Report back** per operator's required format (branch+commit range, full assertion table vs operator's original, kept/corrected/dropped rationale for A-H, cross-path agreement rate, written `--strict` criterion).

## Also still outstanding from earlier in this session (not T-432 scope but flagged)
- Unconfirmed SSL-certificate push error on the T-432 claim commit to `origin/main` — needs verification/retry.
- CLAUDE.md session-start protocol Q6 ("What are you actually worried about?") was never answered this session.

## Key facts to not re-derive
- Portfolio cache field names: `mid_price_at_entry`, `vig_at_entry`, `gross_edge`, `fee_net_edge`, `fee_per_contract`, `kalshi_threshold`, `entry_price_paid`, `contracts` (float, ADR-0050 epoch>=12 T4M-PROJ only), `status`, `outcome`, `pnl`, `resolved_at`, `actual_hits`, `logic_epoch`, `band`.
- T1 gross_edge = `model_p - mid - vig/2` (half-vig). T4M-PROJ gross_edge = `model_p - mid - vig` (full vig, always YES-frame). ADR-0045/GG-119.
- `logs/t4_mlb_resolved_ledger.jsonl` is a SLIM/renamed export (`edge`/`mip`/`vig`), schema-inconsistent with portfolio caches — script uses portfolio caches only, not this file.
- Assertion A (ticker date == game_date) is a LIVE regression, not legacy residue: 438/627 (69.9%) violations concentrated in current epoch 12 — corroborates GG-170 (OPEN).
