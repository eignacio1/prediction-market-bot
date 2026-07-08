# GG-100 Diagnosis — the ANTI-PREDICTIVE result is a GG-077 fee-sign artifact, NOT a no-alpha verdict

**Date:** 2026-07-08 · **Context:** T-256 repointed `run_t177_edge_monitor.py` at the live MLB book; first run (n=169) returned ANTI-PREDICTIVE (Fisher p=0.0236, OR=0.350), flagged as a G6-gate threat (GG-100).
**Verdict:** the monitor uses the **stored** `fee_net_edge`, which is YES-framed and wrong-signed for NO-direction bets (GG-077). The book is 157/169 NO, so ~93% of positions are mis-cohorted and the Fisher test inverts. Recomputing edge direction-aware voids the anti-predictive finding.

## Reproduction (on the live n=169 book, `logs/.vps_portfolio_cache_mlb.json`)

| Method | edge>0 cohort | edge≤0 cohort | Fisher p | verdict |
|--------|--------------|--------------|----------|---------|
| **Stored edge (monitor's method, `run_t177_edge_monitor.py:127`)** | n=29, wr 0.276 | n=140, wr 0.521 | **0.0236** | ANTI-PREDICTIVE (reproduces GG-100 exactly) |
| **Direction-aware (`compute_fee_net_edge`, GG-077-safe)** | n=166, wr 0.488 | n=3, wr 0.000 | **0.247** | NOT anti-predictive |

The cohort-size collapse (166 real-edge bets → only 29 under stored edge) is the fingerprint of the sign bug: the bot only bets when it sees edge, so almost every position has edge>0 when computed correctly. My earlier EXP-017B direction-aware contrast on the n=151 book gave the same qualitative result (`fisher_edgeGT0_vs_LE0` p=0.245).

## Root cause

`run_t177_edge_monitor.py` line 127: `edge = p.get("fee_net_edge")` — reads stored, never recomputes. This is precisely the trap GG-077 documents and that `run_exp017_mlb.compute_fee_net_edge` was written to avoid. T-256 fixed the *portfolio pointer* but not the *edge computation*, so the monitor was pointed at the right book with the wrong math.

## Important caveats (do NOT over-correct in the other direction)

- **Not anti-predictive ≠ positive alpha.** Direction-aware, the edge≤0 cohort is only n=3, so the Fisher test is essentially uninformative — it rules OUT the anti-predictive artifact, it does not establish edge.
- **The underlying alpha question is still open and currently negative-leaning** — but that is GG-004/variance (aggregate −$44.76 at n=169, sign-flipped from +$15.23 at n=151; edge is variance-dominated per EXP-017B/C), NOT anti-predictiveness. Keep the two separate.
- **Calibration is intact** (EXP-017C: slope CI includes 1) — a calibrated model cannot be genuinely anti-predictive, which is corroborating evidence the ANTI-PREDICTIVE flag was an artifact.

## Recommended resolution

1. Harden `run_t177_edge_monitor.py` to recompute `fee_net_edge` direction-aware (reuse `compute_fee_net_edge`); add a NO-majority regression fixture that catches sign inversion. Re-run → verdict flips off ANTI-PREDICTIVE.
2. Downgrade GG-100 to RESOLVED-as-artifact; do **not** escalate to DS as a no-alpha finding. Cross-reference GG-077.
3. Refresh the stale GG-004 figure (n=151/+$15.23 → n=169/−$44.76) as a separate, still-open variance/sample item.
4. The T-255 per-band monitor MUST be direction-aware from line one — this incident is the proof of why.
