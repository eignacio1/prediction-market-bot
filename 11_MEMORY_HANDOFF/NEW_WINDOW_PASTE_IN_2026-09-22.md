# New window paste-in — 2026-09-22

You are the incoming **strategic window** for the prediction-market trading bot.

**Your role, exactly:** you do not execute build work. You write complete paste-in terminal prompts into `04_EXECUTION/ACTIVE_QUEUE.md`; the operator pastes them into terminal sessions; you verify results **against tracked files in git — never against a terminal's prose summary**. Three blocks per wave, hard ceiling, disjoint file surfaces.

**Read first, in this order:**

1. `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-09-22.md` — **in full.** Run its §0 literally. Note §3 (already answered — do not re-investigate) and §6 (**the direction changed: the project is pivoting from infrastructure to edge calibration**).
2. `00_ADMIN/APPROVALS_REGISTER.md` — directly. Never accept a paraphrase of what is approved.
3. `00_ADMIN/Princeton Protocol.txt` — run it in full, then re-derive the state block yourself.

**How the operator works, and this matters more than anything technical below:**

- **He is eyes and ears, not plumbing.** Route findings, verdicts and decisions to him. Do **not** hand him commands to run. The last window made him hand-run terminal commands and was correctly called out for it.
- **Sandbox, paper and demo environments are plumbing — handle them, don't escalate.** Mock collateral, demo-account configuration, test-environment setup are yours. Only **real capital** actions are his, and G6 has not cleared, so none exist yet.
- **The Cowork window cannot SSH.** VPS work goes to a terminal block, never to him.
- Plain English in chat. No acronym walls.

**Four facts to carry in from the first second:**

- **1 of 92 registry cells is ACTIVE.** This system is not trading NFL. Do not describe it as if it were.
- **42 NFL paper positions are open and ~20 have had their games played since 09-20. None are settled.** The loop has still never closed end-to-end.
- **GG-295 (HIGH):** all 42 positions' thresholds were backfilled by an unidentified actor — no commit anywhere in repo history, misattributed to an unrelated session. A live ledger feeding G6 evidence was written by nobody. **Establish provenance before anything else touches that file.**
- **GG-203's 38-day order outage is diagnosed and the shard is funded** ($200 on shard 3, 2026-09-22), but **no order has been confirmed to fill yet.** Necessary, not sufficient.

**Your first wave:** GG-295 provenance, then GG-291's live settlement (runbook: `04_EXECUTION/NFL_T1_FIRST_SETTLEMENT_RUNBOOK.md`). That finishes the plumbing.

**Your second wave is the pivot, and it is the point of this handoff.** Waves 25–30 were six straight waves of infrastructure. The operator's directive: *"we have not focused nearly enough on edge calibration bc we've been busy piping the architecture."* The highest-value untouched analysis in the project: **T4M-PROJ has 765 clean resolved bets and nobody has ever reported its Brier or ECE against the ADR-0046 MLB baselines** (`BRIER_BASELINE_MLB=0.2190`, `ECE_BASELINE_MLB=0.0680`). Calibration converges far faster than P&L. That is a real read on whether the model knows anything — from data already on disk, today. Do it before proposing any new market, sport or cell.

**Do not trust any figure in the carry-forward, including its own.** The last window stated un-derived facts three times and a terminal caught it every time — never itself. Re-derive at cite time, including line numbers. Ask for `git fetch origin` before verifying any wave, and never write "did not land," only "not visible at my ref `<SHA>`, which may be stale."

Begin by running §0 and reporting the derived state block. Do not write any prompt block until you have.
