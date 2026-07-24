# Session Handoff — 2026-07-24T04:48Z

**Trigger:** Operator-initiated (`/session-end` after "you're free to complete the remainder of your tasks in full — if you're all done, then proceed with /session-end")
**Last commit:** `fac4d1a` (session branch, rebased onto and merged into `main` as `f1a7bf7`) — pushed to GitHub. VPS deploy not applicable (research-only session, no src/ changes).

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** No test-suite changes this session (research/governance-doc only; `scripts/mc_survivable_edge_sweep.py` is a standalone research script, not part of the pytest suite)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (unaffected by this session)
- **Paper bets:** MLB 309/30 resolved (G6 gate already numerically past threshold, still gated on GG-004 sample-adequacy/DS sign-off); NBA 158 resolved, dark/frozen

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Registered GG-135 (MAIN book's real variance × cadence trips the 20% drawdown kill switch ~100%/yr even at zero edge) | Empirical-bootstrap MC replay of MAIN's real per-bet σ (1.081%/bet) at real cadence (15.83 bets/day) shows the risk config self-terminates on variance alone, independent of whether Window A's calibration fix ever lands a positive mean edge | `GOVERNANCE_GAP_LOG.md` GG-135 | Claude (this session) |
| Computed the Kelly-fraction/cadence/DD-width survivable-edge frontier per book, not yet acted on | Answers "what would need to be true" before drafting a remediation ADR — quantifies that Kelly-fraction cuts reduce variance quadratically while cadence cuts and DD-width widening are both roughly an order of magnitude too weak alone | `05_RESEARCH_EXPERIMENTS/MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md` | Claude (this session) |
| Renumbered a session-local "GG-134" to **GG-135** after discovering a concurrent session had independently registered its own, differently-scoped GG-134 and merged first | Live ID-collision, same failure class as GG-113/GG-129→130/GG-131→132; established convention is to renumber the unmerged side with an explicit provenance note, never touch the already-merged entry | `GOVERNANCE_GAP_LOG.md` GG-135 Gap-ID field, `DECISION_LOG.md` 2026-07-23 row | Claude (this session) |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| B1 — register ruin-geometry governance gap | ✅ GG-135 registered (renumbered from collided GG-134), `DECISION_LOG.md` note appended |
| B2 — survivable-edge frontier sweep, both books | ✅ `scripts/mc_survivable_edge_sweep.py` (new) + `05_RESEARCH_EXPERIMENTS/MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md` (new): MAIN needs +0.169%/bet edge for 1yr P(kill)≤10% at today's sizing (~27x best observed cohort mean); T4 needs ≈−0.0005%/bet (already near-survivable, edge-limited not ruin-limited) |
| GG-ID collision resolution | ✅ Renumbered GG-134→GG-135 throughout, two-round rebase against `origin/main` resolved (both `GOVERNANCE_GAP_LOG.md`/`DECISION_LOG.md` are deliberately non-`merge=union`, so this required manual conflict resolution keeping both sessions' entries) |
| PR #50 opened and merged to `main` | ✅ Merged `f1a7bf7`, `MERGEABLE`/`CLEAN` confirmed pre-merge |
| Progress tracker | ✅ `04_EXECUTION/ITERATION_MC_PROGRESS.md` (new) — B1/B2 completion lines, corrected post-rebase to reference GG-135 and commit `78f2967` |
| Nav files updated | ✅ `TODO_NEXT.md`, `MEMORY_BANK.md`, `PLAN.md` all carry a fresh "Last reviewed" entry for this session |

---

## ONE THING PENDING

**Window B3 — draft the ADR superseding ADR-0040 with variance-aware sizing for MAIN — is NOT started.** It is explicitly gated on Window A2's post-fix edge estimate (a different, not-yet-landed workstream), per `ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md`'s resume-gate #2 ("B frontier shows the risk config admits survival at the post-fix edge"). Nothing is running and nothing is cached waiting on this — B3 simply has no valid inputs yet. When Window A2 lands, substitute its real edge estimate into `MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md`'s Part A/B (currently only illustrative brackets at 0%/+0.02%/+0.05%/+0.10%/+0.20% per bet) before drafting the ADR.

---

## Current Paper Portfolio

- **MLB (MAIN + T4 combined book, per ADR-0035/ADR-0037 dual-ledger):** Bankroll $759.81 (26 open, 0.0% drawdown, +$21.16 P&L) — carried forward unchanged from T-395's last pull; not re-pulled this session (research-only, no bet-affecting change)
- **NBA:** Bankroll $751.10 (0 open, 24.9% drawdown, historical/frozen — dark per standing operator directive)
- Closed/Resolved: MLB 309 | NBA 158 — G6 gate: 30/30 numerically (still gated on GG-004 sample-adequacy standard, not a raw count)

---

## Active Cron on VPS (157.230.91.33)

Unchanged by this session — see `MEMORY_BANK.md`/CLAUDE.md Step 4 for the live schedule (T1 MLB, T4 MLB systemd, T1/T2 NBA dark).

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016) AND GG-004 sample-adequacy standard (APR-0024, variance-derived `n*`) is cleared per band
3. **GG-135 is a live, unresolved risk finding, not just a research note:** MAIN's current risk config (Kelly fraction, DD-switch width, cadence) will very likely trip the permanent 20% drawdown kill switch within a year even if Window A's calibration work succeeds in finding a small positive edge — because the required edge (+0.169%/bet) is ~27x anything observed so far. Any session reasoning about MAIN's near-term trajectory should treat this as the dominant risk, not calibration quality.

---

## ⚙️ DECISION AUDIT

**Step 1 (`decisions_logged: false` scan):** Not re-run this session (no `02_ARCHITECTURE_DESIGN/`, `08_MODEL_RISK_GOVERNANCE/`, or `01_SPEC/` documents touched).

**Step 2:**

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `GOVERNANCE_GAP_LOG.md` (GG-135) | N/A (not a `decisions_logged`-tracked doc) | 2026-07-23 row, DECISION_LOG.md | ✅ |
| `05_RESEARCH_EXPERIMENTS/MC_SURVIVABLE_EDGE_FRONTIER_2026-07-23.md` | N/A (research artifact, not a governed spec doc) | Referenced from DECISION_LOG.md row | ✅ |

Sprint/session closed — no `false` rows without a registered follow-up.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260724_0448.md.
# Window B1/B2 are done and merged (PR #50, GG-135). Window B3 (ADR superseding ADR-0040 with
# variance-aware sizing) is next but gated on Window A2's post-fix edge estimate — check whether
# that has landed before starting B3."
```
