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

## Later the same day (T-429)

**What changed today, in one paragraph:**
Two separate problems got fixed. First, the live-game data feed for baseball (ESPN) had started rejecting our requests, which meant the fast, in-game betting layer was flying blind — that's fixed and confirmed working again. Second, and more serious: we found that the system had been resolving a large chunk of baseball bets against the wrong day's final score. Picture betting on a Tuesday game but the system accidentally grading it using Wednesday's box score instead — over half of all closed bets in this program had that flaw. We fixed both the part that was writing the wrong date down and the part that was reading it, and then went back and corrected the historical records — about 1,440 of them — so today's ledger reflects the right game for every bet. While double-checking that fix against an independent, second copy of the game outcomes we keep, we confirmed the fix worked, but we also found a second, different, and still-unexplained mismatch between our two record-keeping systems on a chunk of bets. We don't yet know why. That's now a clearly written-down, ready-to-pick-up task for next time, not something anyone is actively chasing today.

**What this means for your money:**
No change to money at risk — still paper trading only, zero real capital. This does mean some of the win/loss numbers we've been reporting for the baseball live-betting strategy were graded against the wrong day and are being treated as unverified until the follow-up work is done — nothing about the pregame baseball numbers (the ones closest to the $30-bet finish line) is affected by this.

**Does anything need your decision right now?**
No. Both fixes are done, tested, and will go live once this branch merges (happening right after this digest).

**Anything that worried the session, even if not urgent:**
Yes — the size of the wrong-date problem was much bigger than first suspected (over half of closed bets, not the smaller slice originally assumed), and there's a second, still-unexplained discrepancy sitting underneath it that we haven't root-caused yet. Both are written up in detail for the next session to pick up; neither touches live capital since none exists yet.

---

*Full technical detail: see `SESSION_HANDOFF_20260807_0016.md` and `DECISION_LOG.md` for 2026-08-06 (T-427), plus `SESSION_HANDOFF_20260807_0610.md` and `DECISION_LOG.md` for 2026-08-07 (T-429), plus `05_RESEARCH_EXPERIMENTS/T427_REPLAY_DETERMINISM_AUDIT.md`.*
