# Operator Digest — 2026-09-29

- T-579 (auto): T-579 (36.3) — landed Wave 36 queue, activated GG-303 write fix under authorization (running-process proof only, audit-log leg not yet demonstrated — no live game state), completed Operator Console Section 0 (7/7 counts), full Q1-Q7 adversarial pass clean.
- T-580: Wave 36 Block 36.2 — gave T4 MLB "eyes" on score/leverage state. All 6 ESPN game-state fields were already in the polled payload but discarded; now logged (model output `p_t4` proven unchanged — logging only). Built an offline walk-off-leverage-shrink candidate model, not wired live. The A/B validation gate (ADR-0042) could not be run today — no non-forbidden T4 resolved-bet cohort exists (T-577 cohort is off-limits, 2026 season closed) — reported as the honest result, not a failure. ADR-0065 drafted, PROPOSED only. Merged to main (`ea48d57`). Flag: stray branch `session/20260924T045227Z-resolved-filter` (7 commits, 4 days old, not this session's) found NOT LANDED by the branch sweep — not touched, needs owner follow-up.

## T-582 — governance housekeeping (recording only)
- Your 2026-09-29 approval of 36 earlier decisions is now written into the approvals register as one entry. Nothing was approved or changed; the ten items waiting on you are still waiting.
- Found that the automatic register checker only notices 7 of those 36 missing entries; logged as a new gap (GG-312).
- Filed 25 finished gap records into the archive, unchanged, and deleted 23 old merged branches. 26 branches were left alone (in use by other sessions, or not merged).
- Still zero real money at risk. 17 old unmerged branches on the server are yours to route.
- T-583 (auto): T-583 built a parallel T4 A/B harness (game-clustered paired Δ-Brier, loud refusals incl. T4M-PROJ); no real cohort scorable until 2027.

## T-581 — EXP-027 EPA splits (STANDARD)
- I built passing/rushing EPA splits as an offline candidate model for NFL moneyline. It is not wired into anything and the default model is unchanged.
- The splits were already downloaded but discarded during cleanup, so I recovered them from the same nflverse file. No new data source.
- Result: no detectable improvement. Every confidence interval spans zero. The sample (14–16 bets vs ~2,610 needed) is the real limit, and more features cannot fix that.
- ADR-0066 is drafted as PROPOSED. I recommend not accepting it.
- Needs your decision: whether to schedule an NFL T1 cron (I added none), and whether to source historical moneylines for a bigger closing-line test (2026 has only 48 games).
- I did not touch the governance gap log or decision log (37.3 owns them). Concerns for it are in the handoff.
- T-584 (auto): T-584 GG-312 parity checker fixed both directions; all 36 ratified ADRs covered; Section 0 15->5.
