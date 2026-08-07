# Operator Digest — 2026-08-07

**What changed today, in one paragraph:**
Before letting the team start rebuilding a piece of the betting-record code, we asked it to prove something first: if you re-run history through the current code, do you get back byte-for-byte the same betting records you actually have on file? The honest answer turned out to be "no, and it can't, and that's fine." The reason is good, not bad: three different times in the past, we fixed a real pricing-cost bug in how fees get calculated, and each fix changed the formula going forward without rewriting old records — which is exactly the discipline we want (old decisions get frozen, not silently rewritten). That means a record from before a fix and a record from after it were correctly calculated by two different formulas, on purpose, so replaying everything through today's single formula will never match the oldest records exactly. We rewrote the goal to match that reality — instead of "everything must match exactly," it's now "everything must match exactly once you account for the three known, on-purpose formula changes" — and confirmed on real data that once you do that, the numbers line up.

**What this means for your money:**
No change — still zero real money at risk. Nothing about today's work touched live trading logic, risk limits, or the go-live gate. This was a pre-check before a future rebuild, not the rebuild itself.

**Does anything need your decision right now?**
No — nothing needs you today. This was a scoped, read-only investigation and it's fully closed out.

**Anything that worried the session, even if not urgent:**
No new concerns from today's work itself. Two pre-existing, unrelated housekeeping items were noticed in passing (a numbering-consistency check and a stale navigation-document check) but deliberately left untouched, since today's task was scoped narrowly and touching them would have gone outside that scope — flagging for a future session to pick up.

---

*Full technical detail: see `SESSION_HANDOFF_20260807_0016.md` and `DECISION_LOG.md` for 2026-08-06, plus `05_RESEARCH_EXPERIMENTS/T427_REPLAY_DETERMINISM_AUDIT.md`.*
