# T-588 (wave 39.2) — Evidence boundary: census, predicate, delta

**Date:** 2026-09-30 · **Tier:** STANDARD · **Status:** measured, applied nowhere. Read-only on every pool. Gaps: GG-317 (updated, still OPEN), GG-318, GG-319 (new).

Source: read-only copies of six live VPS files (sha256 in the session scratchpad `SHA256.txt`, recorded after copy). Reproduce with `python3 scripts/evidence_boundary_census.py --pool-dir <dir>`. Nothing was modified, moved, quarantined, deleted or backfilled.

## The predicate

`is_countable_evidence(row, band)` in `src/prediction_market_bot/logic_epoch.py`. True only when the row is epoch-clean for the band (via the unchanged `is_clean_for_band`; UNTAGGED requires `CURRENT_LOGIC_EPOCH`, as the monitor does) AND `evidence_class(row) == MODEL_EVIDENCE`. Fails closed on non-dict rows, missing/non-int/bool epochs, STUB, UNATTRIBUTED, and any `model_identity` not on the registered-real-model list (currently one entry: `EXP-027 LR`). Tests (`tests/test_evidence_boundary.py`, 21 passing, plus 73 passing with `test_band_monitor` and `test_backfill_logic_epoch`) cover (a) STUB with valid epoch = False, (b) UNATTRIBUTED (absent/None/empty/"UNKNOWN"/non-string) = False, (c) MODEL_EVIDENCE with pre-floor epoch = False. It is wired into nothing.

## D1 — Census by evidence class (read-only)

| Pool / section | Class | Rows | model_identity values | Epochs | Bands | Rows with run_id |
|---|---|---|---|---|---|---|
| MLB T1/T2/T3 / open_positions | UNATTRIBUTED | 17 | {'<absent>': 17} | 1-8 | {'T1': 17} | 0 |
| MLB T1/T2/T3 / closed_positions | UNATTRIBUTED | 468 | {'<absent>': 468} | 1-8 | {'T1': 466, 'T2': 2} | 0 |
| MLB T1/T2/T3 / rejected_positions | UNATTRIBUTED | 16 | {'<absent>': 16} | 3-3 | {'T1': 16} | 0 |
| MLB T4M-PROJ / open_positions | UNATTRIBUTED | 63 | {'UNKNOWN': 63} | 12-12 | {'T4M-PROJ': 63} | 0 |
| MLB T4M-PROJ / closed_positions | UNATTRIBUTED | 3923 | {'<absent>': 2994, 'UNKNOWN': 929} | 1-12 | {'T4M-PROJ': 3558, '<none>': 365} | 0 |
| MLB T4M-PROJ / rejected_positions | UNATTRIBUTED | 2000 | {'UNKNOWN': 2000} | 12-12 | {'T4M-PROJ': 2000} | 0 |
| NFL T1 game-market / open_positions | MODEL_EVIDENCE | 22 | {'EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)': 22} | 12-12 | {'<none>': 22} | 0 |
| NFL T1 game-market / open_positions | STUB | 802 | {'STUB (StubNFLForecastModel — NOT a trained model, GG-255)': 802} | 12-12 | {'<none>': 802} | 802 |
| NFL T1 game-market / closed_positions | MODEL_EVIDENCE | 20 | {'EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)': 20} | 12-12 | {'<none>': 20} | 0 |
| NBA T1 (dark) / closed_positions | UNATTRIBUTED | 158 | {'<absent>': 158} | none | {'<none>': 158} | 0 |
| NBA T4 (dark) / closed_positions | UNATTRIBUTED | 2895 | {'<absent>': 2895} | none | {'<none>': 2895} | 0 |
| MLB T4M-PROJ resolved ledger (monitor source, WIN/LOSS only) | UNATTRIBUTED | 3923 | {'<absent>': 3923} | 1-12 | {'T4M-PROJ': 3923} | 0 |

## D3 — clean_n today vs under is_countable_evidence() (computed, NOT applied)

| Cell:Band | raw_n | clean_n today | clean_n countable | difference |
|---|---|---|---|---|
| mlb_player_prop_hits:T1 | 466 | 0 | 0 | 0 |
| mlb_player_prop_hits:T2 | 2 | 0 | 0 | 0 |
| mlb_player_prop_hits:T4M-PROJ | 3923 | 1694 | 0 | -1694 |

## Reading the D3 table

**T4M-PROJ goes from 1,694 clean rows to 0.** That is the finding, and it does not mean the predicate is wrong. The 1,694 epoch-12 rows are the 929 closed rows whose writer stamped the literal `UNKNOWN` (GG-318) plus 765 rows written before the field existed; and the ledger the monitor reads carries no `model_identity` at all (GG-319), so every ledger row reads UNATTRIBUTED regardless of its pool row. T1 (466) and T2 (2) are already 0 today because their epochs (1-8) are below the floor of 10, so they lose nothing.

**Which route:** a provenance-established allowlist, not a weaker predicate and not a backfilled field. Concretely: named, dated runs of the T4M-PROJ writer, evidenced from git history and audit events, admitted explicitly as MODEL_EVIDENCE. Backfilling `model_identity` from the pool by position_id, or from the epoch's `approval_commit`, would manufacture provenance the rows do not carry (GG-228). Until an allowlist exists the countable T4M-PROJ n is 0 and should be reported as 0. Whether to build the allowlist, and whether to flip any counter, is the operator's decision.

Also observed: the only rows with a real `run_id` anywhere are the 802 STUB rows. The 20 closed NFL EXP-027 rows have `model_identity` but no `run_id` (run provenance may be dropped on close; UNVERIFIED, noted in GG-319).

## Can a stub row still enter a clean_n after this block?

Yes. This block adds a predicate and wires it nowhere, so every counter counts exactly as before. Two things are true today. (1) The 802 NFL STUB rows are not in any monitored cell: `run_band_monitor.py` reads only the MLB portfolio and the T4 ledger, so its printed clean_n cannot include them. (2) Any counter that reads the NFL pool through `is_clean_for_band()` would count all 802, because their epoch is 12, at or past every floor. The epoch-only call sites are `run_band_monitor.filter_clean` (`scripts/run_band_monitor.py:252`), `run_power_calc.py:192`, `mc_forward_projection.py:355`, and about a dozen analysis scripts calling `is_clean_for_band` directly (`t573_*`, `t577`, `t431`, `t437`, `t565`, `t571`, `run_t426`, `measure_archive_spread_by_series`); `assert_ledger_invariants.py` also imports it. The MLB game-market stub is a separate leak: `StubMLBGameMarketForecastModel` has no `PROVENANCE` and stamps `UNKNOWN`, which classifies as UNATTRIBUTED, not STUB; under the epoch-only path it counts, and under the new predicate it is excluded only because unknown fails closed. The write-boundary that stops stub rows being written at all belongs to 39.1 (`paper_trader.py`) and was not touched.

## Source file sha256 (copies read)

```
19a1cf7771ab0dda8aad95e66409afba473e3bdafa12d361cf6bf946976831a1  paper_portfolio_mlb.json
27ec31e87f80706ce9319ad03d6ae940dcf64da501f9b2554239ceabed7d7878  paper_portfolio_mlb_t4.json
47dab9c8f6888a2f99caa8fecbf3aeaea1908f630e89dd9e402547878144e9d7  paper_portfolio_t1_nfl_game_market.json
b9019cdcb71efe213a8c2abf385560743cf42bb1ce94ba889231c78543c0fc76  paper_portfolio.json
543826f60afc977fd897dc5d697695e5e42d0183f31385ad05bf2d342e4dbaa5  paper_portfolio_t4.json
99a6308f805c786f765415634eb1d7d96eb62dd196352dece642b67cfc879b22  t4_mlb_resolved_ledger.jsonl
```
