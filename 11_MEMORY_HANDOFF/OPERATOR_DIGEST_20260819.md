# Operator Digest — 2026-08-19

**What changed today, in one paragraph:**
We wrote up the decision document for how the bot will keep its different bet types (moneyline, run line, totals, etc.) from tangling with each other once we add more of them — one shared record book with a label per bet type, epoch resets scoped so fixing one bet type doesn't wipe out the evidence collected for all the others, and (per your sign-off) a cap on how much we can have riding on any one game across all bet types at once, so three correlated bets don't quietly become one 3x-sized bet. We also checked on last week's separate project (a runs-scored data store for totals betting) and found it was built but never actually merged into the live codebase — it's sitting on a side branch, unfinished business for its own session.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears. Nothing in today's work touched live trading logic, bet sizing, or the kill switch.

**Does anything need your decision right now?**
Yes — the isolation decision document (ADR-0054) is ready for you to read and sign or reject. It covers the four open questions from your prior sign-off session. Ask for it by name next time and I'll walk you through it.

**Anything that worried the session, even if not urgent:**
The runs-scored data store from last week never made it into the main codebase — worth flagging since it might look "done" from the task list alone.

---

*Full technical detail: see `SESSION_HANDOFF_20260819_0435.md` and `DECISION_LOG.md` for this date.*
