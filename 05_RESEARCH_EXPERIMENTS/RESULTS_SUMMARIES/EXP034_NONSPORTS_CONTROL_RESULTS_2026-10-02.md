# EXP-034 — Kalshi non-sports control arm: results summary (CLOSED AT D2 — D1(b) GATE FAIL)

**Verdict on record: D1(b) gate FAIL under the frozen rules (commit 38b8490, unchanged). Every candle-based number in EXP-034 is VOID. D3-D6 not run.**

## Sample (D0)
12 tickers fixed at round 0 (KXHIGHNY, KXHIGHCHI, KXHIGHMIA, KXCPI, KXPAYROLLS, KXGDP; first 2 open each). 7 rounds, 19:33:05Z to 21:41:11Z, gaps 21.2-21.6 min. 84 rows, sha256 ecdf866c66aac8c3b1d2cf39e685062c1e6dff0a2dcd435e15a80c7a6c9eab2c. Sampler PID 63247 ran to completion. Candles pulled after last round + 10 min (21:51Z). No amendment needed (>= 6 rounds). Commit 0f5de4e superseded (equivalent content on origin/main as 1c9703f).

## Gate result (as run)
56/84 pairs pass (66.7%); gate needs >= 95%. Worst measurable miss 0.0000. 28 pairs UNMATCHED, all KXPAYROLLS-26NOV-T90000/T80000 and KXGDP-27JUL29-T4.0/T3.5 (all 7 rounds). The 56 matched pairs (KXHIGH* x 6, KXCPI x 2) all pass with zero miss: 28 exact-candle matches, 28 prior-close matches. Full pairs: `d1b_gate_result.json`.

## Why UNMATCHED (disclosed; does NOT change the verdict)
The runner pulled candles for [first read - 1h, last read + 15m]. These four tickers are thinly quoted and emitted NO candle in that window; the frozen rule says "nearest EARLIER candle, if none exists UNMATCHED", and the runner's 1h lookback made "none exists" true by construction. That lookback was an implementation choice of mine, not in the frozen text.
**Post-hoc diagnostic (run AFTER seeing the FAIL; read-only; 60-min candles, 30-day lookback; `d1b_posthoc_diag_60m.json`):** the prevailing earlier close equals the live read exactly for all four tickers (PAYROLLS T90000 0.30/0.40, T80000 0.37/0.47; GDP T4.0 0.05/0.15, T3.5 0.12/0.22; last candle 10.6-25.6h before round 0). So the failure is a pull-window artifact, not evidence that candles misstate quotes. I did NOT re-run the gate with a wider window: that is a post-result change to how a frozen rule is executed. Whether a corrected-window re-run counts is an OPERATOR / 46.1 decision.

## Relation to GG-333
EXP-035 Part 1 failed G2-G5, G7 on MLB archive comparisons; this gate is independent (different series, live-read reference). Here the matched-pair evidence is clean (56/56 within tolerance, incl. the prior-close rule 46.1 suspects), and the failure is entirely the window artifact above. 46.1's GG-333 diagnosis was not on origin/main at close (checked), so I cannot say whether it bears on this gate. Nothing was adjusted because of GG-333.

## Not run
D3 inventory, pre-registration, D4 back-capture/measurement, weather benchmark, coherence tests: not started. No outcome statistic exists. No CANDIDATE-PENDING-CAPACITY, no coherence cell, no forecast comparison. No cost/fee-at-entry finding. Fee PDF still unread (GG-332).

## GAPS FOUND — FOR REGISTRATION BY 46.1 OR WAVE 47
1. Frozen D1(b) text under-specified the candle lookback; "none exists" was implementable as a window artifact. Future gate pre-regs must fix the lookback.
2. Operator decision: re-run D1(b) with full-lookback matching (needs a new frozen amendment + new sample), or accept FAIL and close the arm.
3. `exp_output/` raw stores are gitignored; the quote file is not reproducible from git (hash in D1B_SAMPLE_MANIFEST.md only).
4. Q7 `assert_ledger_invariants.py` reports SOURCE_UNAVAILABLE in worktrees (VPS caches absent) — Q7 is a silent no-op outside the main tree.
5. Remote branch `session/...-kalshi-nonsports-control` holds a stale pre-rebase line (0f5de4e); work pushed to `...-w46` instead of force-pushing.
6. Q6: T1 MLB shows 0 players/bets on recent runs and T4 cycle-log is 18h old — consistent with season end, but unconfirmed; `SemanticFloorViolation`=1, `CONTAMINATION_HALT`=162168 in audit JSONL (cumulative, game-end expected).
