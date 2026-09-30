# T-592 / Wave 40.2 — Can T4M-PROJ run provenance be established from the record?

**Answer: yes, conditionally, for all 1,694 epoch-12 clean rows.** The record fixes which committed code each of the 13 `t4-mlb` processes contained, and that code's T4M-PROJ formula is byte-identical across all 13 commits. It does not fix the working tree or the pregame input (L1, L2 below). Nothing was applied: `is_countable_evidence()`, `logic_epoch.py`, `run_band_monitor.py`, every ledger and every pool are untouched, and the allowlist is wired into nothing.

## D0 — Sync
Session start: main-tree HEAD `9f2b837`, origin/main `0870f14`. Worktree branch base after claim rebase: `a683eee`. origin/main at close is recorded in the commit/push output in the session log. Claim: T-592 (T-591 was double-claimed by a concurrent session one second earlier; released in `SESSION_CLAIMS.md`).

## D1 — What ran (from the record only)
Chain, per row: `forecast_id` `T4-MLB-C<cycle>-<hash>-…` → `cycle_id` → `session_id` (VPS `t4_mlb_cycle_log.jsonl`, 23,754 cycle ids, 115 sessions) → first-row time → latest `Started t4-mlb.service` in the VPS journal at or before it → VPS `git reflog` HEAD at that instant → `git show <sha>:run_t4_mlb_live.py`.

Checks that passed: all 1,694 rows map to a session (0 unmapped); every row's `entered_at` lies inside its own session's first/last cycle-log timestamps (0 outside); sessions do not overlap; no `Started` event falls inside any window (session_id is per-process); no reflog `reset`/`checkout` falls in any window; the VPS tracked tree is clean today (`git status`, untracked `exp_output/` only).

| Win | Session | Process start (UTC) | Commit the process held | Rows | HEAD moved after start (not loaded) |
|---|---|---|---|---|---|
| W01 | T4-MLB-591DFBAD | 07-31 19:38 | 0bc269eb | 3 | – |
| W02 | T4-MLB-FE41CC24 | 07-31 21:14 | 20142502 | 75 | – |
| W03 | T4-MLB-3F2695DD | 08-01 23:03 | 93efca2a | 32 | 2f13b4bf (08-01 23:05) |
| W04 | T4-MLB-E726FE66 | 08-02 00:08 | cbd09ae8 | 77 | fc44594f, 2b9917fb, 32fb868a (08-04 00:45–00:55) |
| W05 | T4-MLB-06538707 | 08-07 05:26 | 687bf9e0 | 578 | – |
| W06 | T4-MLB-09D88074 | 09-22 06:55 | 2387814b | 140 | – |
| W07 | T4-MLB-A2D81226 | 09-23 06:14 | 7f6e0c78 | 130 | – |
| W08 | T4-MLB-85DBFA89 | 09-24 00:34 | e71fda5f | 19 | – |
| W09 | T4-MLB-F3276022 | 09-24 00:52 | 14091b3f | 77 | – |
| W10 | T4-MLB-E9D58C50 | 09-24 05:16 | 484b405e | 129 | – |
| W11 | T4-MLB-89F36A4B | 09-25 01:41 | 1da5865c | 11 | – |
| W12 | T4-MLB-9FC5E7E4 | 09-25 02:15 | 7493ecd1 | 234 | – |
| W13 | T4-MLB-FD35EF10 | 09-26 06:44 | 7493ecd1 | 189 | – |

Model as of each commit: `p_t4 = p_hits_gte_threshold(h_so_far, threshold, ab_remaining, ba_l10=ba_l10_shrunk)`, a binomial (ADR-0047 shrinkage). The function's source SHA-256 is identical at all 12 distinct commits, and the call site passes `ba_l10_shrunk` at all of them. The 186-line `run_t4_mlb_live.py` change and the `paper_trader.py` changes between `0bc269eb` and `7493ecd1` were checked only for the formula and its call site (both unchanged); the diffs otherwise add a pregame-file helper, a ticker-date helper, logging and write-path changes. In these sessions 87–98% of cycle-log rows carry `ba_l10_shrunk` and in every such row it differs from raw `ba_l10`.

**UNESTABLISHED:** (a) the 2,229 non-clean T4M-PROJ ledger rows (epochs below 12, including all rows before the cycle log begins on 2026-07-02): not reconstructed, since they are not counted today and the cycle log and journal do not fully cover them; (b) VPS working-tree state at each start (L1); (c) the provenance of each day's `pregame_mlb_*.json` (L2).

## D2 — The allowlist
`05_RESEARCH_EXPERIMENTS/provenance/t4m_proj_provenance_allowlist.json`: 13 entries, one per session above. Each carries time bounds, full commit SHA, asserted identity `T4M-PROJ Binomial (ba_l10_shrunk, ADR-0047)`, the function hash, and a four-part citation (journal start, reflog line, cycle-log session extent, git blob). The loader refuses an entry with an empty citation part, a short SHA, or an overlapping window (tested). Limitations L1–L4 are stored in the file itself. The identity string is a proposed label for the operator to approve; it is not in `REGISTERED_MODEL_IDENTITY_PREFIXES`.

## D3 — Recompute (`scripts/provenance_allowlist_recompute.py`; baseline is `evidence_boundary_census.run()`, imported)
| Cell:Band | raw_n | clean_n today | countable without | countable with | recovered |
|---|---|---|---|---|---|
| mlb_player_prop_hits:T1 | 466 | 0 | 0 | 0 | 0 |
| mlb_player_prop_hits:T2 | 2 | 0 | 0 | 0 | 0 |
| mlb_player_prop_hits:T4M-PROJ | 3923 | 1694 | 0 | 1694 | 1694 |

Recovered 1,694 of 1,694 epoch-clean rows (100%); 43.2% of the 3,923 raw rows. Per-window recovered counts equal the Rows column above. T1 and T2 recover nothing: they have no epoch-clean rows, so provenance is moot there. The overlay admits only UNATTRIBUTED rows carrying no identity or the literal `UNKNOWN`; a STUB or any other identity string is never admitted.

## D4 — Does GG-319 make this unrecoverable?
No, but the fix is not the monitor. Evidence: `scripts/build_t4_resolved_ledger.py:120-145` builds each ledger row from an explicit field list that includes `logic_epoch`/`approval_commit` but not `model_identity`. `run_band_monitor.load_t4_ledger` does `dict(p)`, so it would keep the field if the builder wrote it. The monitor's source therefore need not change. What has to change, in order: (1) the run path must stamp a real identity: `paper_trader.py:632` writes `approval.get("model_identity") or "UNKNOWN"` and `run_t4_mlb_live.py` never sets `model_identity` (grep: no hit), which is why every new row is `UNKNOWN`; (2) the ledger builder must pass it through; (3) `REGISTERED_MODEL_IDENTITY_PREFIXES` in `logic_epoch.py` must list the identity with a citation. Until then the historical rows are recoverable only through this overlay, by time window, because no field on any row can carry the fact (GG-228).

## Gaps found (not fixed, not registered here; 40.1 owns the logs)
- **G-A:** the T4 run path never stamps `model_identity` (above). All post-epoch-12 rows keep coming in `UNKNOWN`.
- **G-B:** `build_t4_resolved_ledger.py` drops `model_identity`.
- **G-C (time-sensitive):** provenance rests on the VPS reflog and journal, which git and journald prune. Git's default reflog expiry is 90 days, so W01's reflog line (2026-07-31) ages out around 2026-10-29. Nothing in the repo snapshots it. No audit event, cycle-log row or session-start record carries a commit SHA.
- **G-D:** `pregame_mlb_*.json` (the model's input) is not commit-pinned or hashed.
- **G-E:** Q7 in this worktree reported 0 violations only because its cache files are absent (SOURCE_UNAVAILABLE): a vacuous pass.

## D5 — Operator paragraph
Of the MLB season's 3,923 T4M-PROJ resolved rows, 1,694 are epoch-clean, and today 0 are countable. The record supports admitting all 1,694, in 13 windows, each cited to a journal start, a reflog HEAD and a git blob whose formula is identical across every commit. Approving the allowlist would make 43.2% of the raw season, and 100% of the clean cohort, honestly countable as far as the code is concerned. It does not vouch for the VPS working tree at the time (L1) or for the pregame ba_l10_shrunk input (L2); sign-off should decide whether those two are acceptable residual risk. The other 2,229 rows cannot be recovered by this route and are not proposed. To make the future countable without any allowlist: stamp a real identity in the T4 run path, pass it through the ledger builder, and register it in `logic_epoch.py`. Separately, snapshot the VPS reflog and journal into the repo before about 2026-10-29, or W01 loses its citation.
