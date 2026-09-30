# T-595 / Wave 41 — provenance preservation (results)

Block owner of GOVERNANCE_GAP_LOG.md and DECISION_LOG.md this wave. Nothing backfilled, rewritten, relabeled,
quarantined or deleted (GG-228). No service restarted; no VPS log rotated; no sizing touched; allowlist not applied.

## D0 — land 40.3
Before `8500627`, after `6d29962`; original 40.3 tips `adbe4d7` and `bfd4c4d` preserved in the message.
Ordering note: D0 landed before the gap-log commit (`f87fcd5`).

## D1 — snapshot + offline re-validation (`9d36ba7`)
`05_RESEARCH_EXPERIMENTS/provenance/snapshot_2026-09-30/`: 19 files + MANIFEST.json (sha256 each): full HEAD reflog
(from 2026-05-29), full t4-mlb journal (from 2026-06-27), blob object ids, 12 committed copies of
`run_t4_mlb_live.py`, cycle-log session extents, host fingerprint.
`python3 scripts/verify_provenance_snapshot.py` → **13/13 windows validate from the snapshot alone** (journal Started
event, reflog HEAD at start, no reset/checkout in window, post-start head moves, extents, blob id, function-segment
sha256, call-site `ba_l10=ba_l10_shrunk`, manifest). Tests: `tests/test_verify_provenance_snapshot.py`.
**Not captured:** the 201,875,395-byte cycle log itself (extents only). The reflog expires by default at 90 days, so the
VPS-side W01 citation ages out ~2026-10-29; the snapshot is now the record. Registered as GG-321.

## D2 — forward model_identity (`763939a`)
Before (live-path evidence, real `PaperTrader.open_position`, `live_path_probe_t595.py`, T4-shaped approval with no key):
- **main** (`paper_trader.py:632`): silently writes `"UNKNOWN"`.
- **unlanded T-589 D6 branch** `session/20260930T001343Z-t4-ledger-durability` (`eed471f`, `fd3fc11`; MERGED: NO, not deployed):
  raises `MissingModelIdentityError` on every T4 open. **That branch must not be merged or deployed before this commit.**

After: (1) T4 run path stamps `T4M-PROJ Binomial (ba_l10_shrunk, ADR-0047)` only when the pregame JSON really carried
`ba_l10_shrunk`; otherwise the distinct label `... ba_l10 RAW FALLBACK ...`. (2) `build_t4_resolved_ledger.py` passes
`model_identity` through verbatim (absent → None, "UNKNOWN" stays). Monitor unchanged. (3) The shrunk label is added to
`REGISTERED_MODEL_IDENTITY_PREFIXES` with citation; fallback label deliberately unregistered.
Forward-only registration and the inert 13-window allowlist are separate mechanisms; the allowlist is not applied.
Tests: `tests/test_t595_model_identity.py` (8) plus affected suites: 296 passed; evidence/epoch tests 36 passed.

**Is a T4M-PROJ row countable from this commit forward without any overlay?** Not yet, in practice.
- `is_countable_evidence` returns True for an epoch-clean row stamped with the shrunk identity, but it is UNWIRED: no
  counter or monitor uses it.
- The stamp is only as true as the code running on the VPS; nothing is deployed in Wave 41.
- Raw-fallback rows and every pre-change row stay UNATTRIBUTED; `run_id` and other run-provenance fields remain "UNKNOWN".
- Missing: deploy (operator), wire the predicate into the counters, and the 39.1 branch decision.

## D3 — claim re-verification (`214d517`, `f68d784`, GG-322)
`claim_session.sh` re-runs `check_id_collision` on every push retry, excluding only its own row; on collision it
withdraws the local claim and exits 1. `check_id_collision` takes an optional `exclude_row`.
`tests/test_claim_session_retry_recheck.py` (3 tests): the race test fails on the old script, passes on the new one.
T-592 not renumbered; ambiguity recorded in SESSION_CLAIMS naming both blocks.

## Hand-backs
- Shared-tree `git checkout HEAD -- CLAUDE.md 02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md 02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md 03_DECISIONS/ADR-0014_per-band-decision-tree-mechanics.md`
  refused: `fatal: Unable to create '.../Prediction Markets/.git/index.lock': File exists.` (PID 33525). Not bypassed.
  Four drafts remain undiscarded in the shared tree (backups in the session scratchpad `shared_tree_backup/`).
- Cross-refs: GG-318, GG-319 (identity dropped by builder; closed for forward rows only).
