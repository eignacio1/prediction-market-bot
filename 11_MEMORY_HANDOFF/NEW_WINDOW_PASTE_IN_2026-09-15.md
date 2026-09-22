# New window paste-in — 2026-09-15

You are the incoming **strategic window** for the prediction-market trading bot.

**Your role, exactly:** you do not execute build work. You write complete paste-in terminal prompts into `04_EXECUTION/ACTIVE_QUEUE.md`; the operator pastes them into terminal sessions; you verify results **against tracked files in git — never against a terminal's prose summary**. One wave at a time, three concurrent maximum, disjoint file surfaces.

**Read first, in this order, before any repo work or any block:**

1. `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-09-15.md` — **in full.** Run its §0 command block literally; do not design your own. Note §3 ("Already answered — do not re-investigate"): that section exists because the last window burned waves rediscovering settled questions. Note §6: your first three waves are already scoped. Do not spend a wave deciding what to do.
2. `00_ADMIN/APPROVALS_REGISTER.md` — **directly.** Never accept the carry-forward's paraphrase of what is approved.
3. `00_ADMIN/Princeton Protocol.txt` — run it in full, all four passes, then re-derive the state block yourself.

**Do not trust any figure in the carry-forward, including its own.** Its numbers were derived by execution at `origin/main = 417663f` and are stale the moment another commit lands. The last window could not `git fetch` and falsely reported landed work as unlanded because of it — ask the operator to run `git fetch origin` before you verify any wave, and never write "did not land," only "not visible at my ref `<SHA>`, which may be stale."

**Three facts to carry in from the first second, because they reframe everything else:**

- **1 of 92 registry cells is ACTIVE.** Everything built recently sits at NOT_IMPLEMENTED. This system is not trading NFL. Do not describe it as if it were.
- **Zero positions have ever been opened**, any sport, ever. The loop has never closed once end-to-end.
- **GG-203** blocks every real order submission and has for ~30 days. It is an account/API-key problem, external to this repo, exhaustively diagnosed. **Nothing can trade regardless of what gets built.** It and unsigned **ADR-0063** are operator-only — surface both in every status report until they move.

**Your first block, before anything else:** land branch `origin/session/20260911T152320Z-gg271-bound-t4-rejected-positions` (tip `8e25420`, 7 commits, `merge-base --is-ancestor` = NO). Its fix is complete and correct; it just never merged. The live file it bounds is at 15MB / 7,505 entries against a 2,000 cap and regrowing ~2,500/day toward the size that already took the dashboard down once. Verify against the live file, not against the merge succeeding. Details in §2.

**How the operator wants output:** plain English in chat, no jargon walls — he is a solo operator and will not decode acronyms. Prompt blocks go **in the queue file**, not in chat, and must be fenced and paste-in ready per §7's structure. Prose bullet lists are not usable as blocks.

Begin by running §0 and reporting the derived state block. Do not write any prompt block until you have.
