# Operator Digest — 2026-07-16 (T-377, "Terminal 2" GG-105 investigation)

**What changed today, in one paragraph:**
You asked for a dedicated deep-dive into the baseball model's most important open problem right now — the finding that its most confident bets are actually its worst ones. This session tried the one fix that's already worked on a similar problem before (the same "soften overconfidence" trick that fixed the basketball model's calibration months ago) and found it does NOT work here — applying it actually makes the pattern worse, not better, even though it does make the model's stated confidence levels more honest on average. That's a useful negative result: it rules out the easy fix and points more strongly at the other, more involved fix that's already been proposed and is still waiting on you. Separately, the session noticed that all four active baseball strategies' "how many clean bets do we have" counters currently read zero at once — this is an expected, temporary side effect of three unrelated bug fixes landing close together this week, not a new problem, and it'll sort itself out as new bets resolve.

**What this means for your money:**
No change — still zero real money at risk. Nothing in this session touched live trading code or moved any dollar figure; it was pure investigation.

**Does anything need your decision right now?**
No new ask today. The pre-existing one is still there: the proposed fix for the overconfidence problem (giving less weight to a player's very recent batting stats, which can look artificially certain in small samples) is still waiting on your sign-off — today's finding makes the case for it a bit stronger by ruling out the alternative.

**Anything that worried the session, even if not urgent:**
One thing worth flagging even though it's not dangerous: right now, none of the four active baseball strategies have enough freshly-resolved bets to run their normal health check — a coincidence of timing from three good fixes landing in the same day or two, not a sign anything is broken. It should self-correct within the next several days as more bets resolve; worth a glance if it's still showing zero a week from now.

---

## Update — same evening (T-376, GG-091 mypy remediation close-out)

**What changed:** This was internal code cleanup, not a trading change. The bot's code has been getting harder for automated safety checks to fully verify over time — think of it like a spell-checker for code that catches places where the program might get confused about what kind of data it's holding. This session fixed the easiest, lowest-risk batch of these (about half of what's been flagged so far) across 42 files, and deliberately left the files closest to your money (the risk sizing and bet-placement logic) untouched for a more careful pass later. Ran the full test suite before and after — same result both times, nothing broke.

**What this means for your money:** No change — still zero real money at risk, same as every day until the gate clears. Nothing about how bets are sized, priced, or placed changed today.

**Does anything need your decision right now?** No — nothing needs you today.

**Anything that worried the session, even if not urgent:** None. The one hiccup — a supporting script used accidentally introduced a typo-like error in 4 files partway through — was caught by an automated check before it went anywhere near the live system, and fixed before anything was deployed.

---

*Full technical detail: see `SESSION_HANDOFF_20260716_0600.md` (T-377 GG-105 investigation), `SESSION_HANDOFF_20260716_2214.md` (T-376 GG-091 mypy remediation), and `DECISION_LOG.md` for 2026-07-16.*
