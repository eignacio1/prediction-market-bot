# Operator Digest — 2026-07-24 (04:50 UTC)

**What changed today, in one paragraph:**
We ran the numbers on how much bad luck alone — not bad predictions, just normal statistical swings — could wipe out the main MLB betting book. The answer: even if our predictions were perfectly break-even (no edge at all), the current bet-sizing and risk settings would very likely trip the permanent "stop everything" safety switch within a year, purely from variance. We also worked out exactly how much real predictive edge would be needed to avoid that (about 27 times better than anything we've measured so far), and which levers actually fix it: cutting bet size helps a lot, cutting how often we bet or loosening the stop-loss barely helps at all.

**What this means for your money:**
No change today — still zero real money at risk, same as every day until the gate clears. This is a finding about the paper-trading risk design, not a live loss.

**Does anything need your decision right now?**
No — nothing needs you today. This session only measured the problem and logged it; the actual fix (likely: reduce how much we bet per position) is a follow-up piece of work that still needs the calibration team's updated accuracy numbers before it can be designed properly.

**Anything that worried the session, even if not urgent:**
Yes, one thing worth knowing even though it's not urgent: the main book's current risk settings are set up in a way that could shut the whole book down on bad luck alone, before we ever get a fair test of whether the predictions are actually good. That's a design gap, not a performance problem, and it's now formally logged so it doesn't get missed.

---

*Full technical detail: see `SESSION_HANDOFF_20260724_0448.md` and `DECISION_LOG.md` 2026-07-23 row.*
