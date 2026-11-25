# SW-9 self-assessment — Princeton Deep Thinking Protocol (Waves 104–126)

**Written:** 2026-11-25 (SW-9, at the operator's request 2026-11-24 18:40 PT: "Assess yourself during this window - against PDTP. Do it
with the full project scope in reference"). Evidence: WINDOW_ERROR_LOG W49–W67, the wave sequencing track, the distance table
(`scripts/distance_to_optimum.py`, 2026-11-25 02:40Z), box reads (d6_read 20261125T0039Z), DECISION_LOG. Feeds the SW-10 handoff (B-125).

## 1. Deconstruction
**Decision:** how well SW-9 served as strategic window over Waves 104–126, judged by pillar movement, steering, error rate, operator
burden, doctrine fidelity and instrumentation — and what SW-10 must do differently. **Ambiguity:** metric (waves shipped vs pillars
moved vs operator burden); causal (window error vs terminal / Muse error vs plain market efficiency).

| P | Subproblem | Lens | Evidence standard |
|---|---|---|---|
| P1 | Did the measures move? | measurement | box reads and the distance table, not handoff prose |
| P2 | Was the right work chosen, before the operator had to say so? | strategy / ops research | operator directives vs wave content, dated |
| P3 | Error rate and pattern | reliability engineering | WINDOW_ERROR_LOG entries, categorized |
| P4 | Operator burden | human factors | catches made by the operator; repeated asks |
| P5 | Doctrine fidelity | governance | DOCTRINE.md vs what was said and built |
| P6 | Instruments and memory | systems | can the window see what it asserts? |

## 2. Sub-solutions + confidence
**P1 — Measures (7/10).** D6 4 → 18 of 117 on the box (NBA 7, NHL 7, NFL 4). Open gaps ~272 → 182. Verdicts issued: H1–H4, H-EDGE-5,
H-MEAS-1, NFL splits (5), pot of gold (18 leaves) — PROOF moved most. Depth: C2 SUPPORTED on an unread season (first factor-driven
forecast gain that held out); MLB engine built; NFL seat N12 applied. Breadth: Kalshi combo families found (B4 registered 5, logging 0).
Execution: flat — no arm clears zero after costs; placement unsupported. Confidence 7: box reads are real; the local distance table
still shows D6 0/129 (leaf_map as of 11-12), unreconciled with the box.

**P2 — Steering (5/10).** Right calls: the edge-location program stated an unstated question and produced the window's main strategic
finding — gross effects keep appearing and dying at the round cost on the most-watched lines; the C2 / combo / MLB turn in W126 followed
from it. Wrong order: W123–W125 were three measurement waves before a build turn; the operator had to say "align your backlog ... we've
talked at length about this" (11-23). The retail-parlay lane (operator 10-16, doctrine since 11-05) reached a block only in W125–W126.
Side-project PAM work went into a wave unasked (11-23). Confidence 5: the counterfactual (build first) is unobservable.

**P3 — Errors (8/10).** 19 logged (W49–W67) in 15 days. Clusters: Muse operations 6 (W59, W60, W61, W62, W65, W66); repeating the
operator's doctrine back or drifting from it 5 (W50, W52, W53, W54, W55); process / tooling 4 (W58, W63, W64, W56); reporting accuracy
3 (W51, W57, W67). Rate rose late: 10 in the last 8 days. Every entry has a fix; several fixes were rules the window then did not run
(the Muse checklist existed and still missed load, W66). Confidence 8: the log is complete for what was caught; uncaught errors are not in it.

**P4 — Operator burden (6/10).** The operator made catches the window should have: "are we set?" asked five times before W66; the
backlog alignment; the gap-burner placement; model sizing (W56). He also had to correct the tone after nulls ("not mayday"). Positive:
blocks paste-ready, decisions routed as one-line approvals, no commands handed to him. Confidence 6 (his time is not measured).

**P5 — Doctrine (7/10).** After W50–W54 the routing language held: no "no edge", nulls closed as hypotheses parked for R&D, pot of gold
treated as an arm. Lapses: doctrine-stack review skipped at wave closes until 11-24; CLAUDE.md window lines four waves stale (fixed
11-24). Confidence 7.

**P6 — Instruments (6/10).** Where the window had instruments (repo, CI, box tasks, `gh`), its claims held. Where it had none (Muse's
browser, the scheduled sweep's setup, cumulative vs per-day counts), it asserted and was wrong (W60, W66, W67). The distance table was
never recomputed at a wave close. Compaction: the window ran on summaries after ~W119; errors per day rose after it. Confidence 6.

## 3. Synthesis and contradictions
- **P3 × P6:** errors concentrate where the window acts without an instrument. Muse is the extreme case: a back-end exchange the operator
  cannot see and the window could read only in pieces. The fix that works is an instrument (`scripts/muse_check.py` with jam / late
  snapshot / slow-queue alarms), not another rule.
- **P2 × P4:** operator catches happen when the window optimizes the local question (measure better) instead of re-reading the north
  star (build the whole board, retail flow first). Each wave lacked one line: "which lane has the operator asked for that this wave
  does not touch?"
- **Contradiction:** the window says the measurement waves were too long (P2), yet they produced the cost-wall finding that justified the
  W126 turn (P1). Both hold: the finding was worth one wave, not three.
- **Contradiction:** "all set" claims (P4) against a P3 record of asserting what it could not see. A claim's confidence should have
  tracked the instrument behind it; it tracked whether a rule had been written.

## 4. Adversarial critique and defense
**Attack:** SW-9 was a strong window: 23 waves, D6 more than four times higher, ~90 gaps burned, the first supported held-out depth
result, the cost-wall diagnosis, a hypothesis doctrine, a Muse queue of ~3,900 chunks. Nineteen logged errors in a project this size is
diligence, not failure; most were caught by the window itself.
**Defense:** the output count is real, but the EXECUTION pillar did not move, no arm clears costs, and the most expensive misses (three
measurement waves, a Muse week at risk, a perishable snapshot lost) were caught by the operator or by consequences, not by the window.
Half the errors were caught only after the operator pushed. **Narrowed claim:** SW-9 was effective at building, verifying in the repo
and logging; it was weak at foresight on systems it could not instrument and at re-checking work against the north star before the
operator did; it degraded late, after compaction.
**Withdrawn:** an earlier implied claim that the Muse failures were mostly Muse's or the platform's (W59 already withdrawn); the W67
"6,300 rows never scored" claim.

## 5. Blind spots (ranked by whether they could flip the verdict)
1. **Self-graded log.** The error log holds what the window caught or was told; terminal-side or Muse-side errors that went unseen are
   absent. Could make the verdict worse.
2. **D6 source disagreement.** Box d6_read 18 vs local distance table 0 (stale leaf map). If the box read over-counts, P1 drops.
3. **Operator time and token cost** of this window are unmeasured; the burden score is inferred.
4. **Counterfactual of build-first** is untestable; P2 could be harsher or kinder.

## 6. Integrated answer and self-assessment
**Verdict: 6 / 10.** Productive and honest in the repo; under-instrumented and over-confident outside it; late in the window, slower to
re-read the north star than the operator. **For SW-10 (B-125):** (1) instruments before claims — recompute the distance table with box
reads at every wave close and reconcile D6; (2) every report states what was verified and what was not; (3) one line per wave: the lane
the operator has asked for that this wave does not touch; (4) Muse changes pass the Monday checklist including load (item 11), and the
nightly check runs; (5) hand off earlier after a compaction rather than run on summaries.
**Weakest point of this assessment:** it is graded from the window's own error log and its own summaries — the same instruments whose
gaps it criticizes.
