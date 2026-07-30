# Operator Digest — 2026-07-29

**Still zero real money at risk.** Nothing was changed today — this was a read-only review you asked for.

**The pregame strategy (T1) is not working, and we can now nearly prove it.** 175 clean bets, losing about 41 cents each. In roughly three days it crosses the threshold where that counts as a formal, on-the-record answer rather than a hunch.

**The live in-game strategy (T4) is a different story, and this is the day's real finding.** There is a bug in the safety check that decides whether a bet is worth placing. It ignores which *side* the bet is on — so when the model is most confident a bet is bad, the check waves it through anyway. Just under half of the recent live bets were placed that way, and they lost $35. The bets the check *should* have allowed made $9. So the live strategy has been graded on a test it was never actually taking.

**What that means:** we don't yet know whether the live strategy works. We had been treating it as failing. It might be — but the measurement was broken, so the honest answer is "unknown," and we need to fix the bug and re-measure before drawing a conclusion.

**Two other things found.** The live bot goes quietly blind after any restart past 8pm Eastern — it keeps reporting itself healthy while watching nothing. One night we lost about 9,700 measurements that way. And the session-start checklist that is supposed to list open problems has been missing 12 of 26 of them, including the most important ones — the more emphatically a problem was written up, the more likely the checklist skipped it.

**Nothing needs a decision from you tonight.** The fixes are written up and queued in order.

---

## Addendum (G1 session, later same day)

Fixed the checklist bug mentioned above — the one that was silently skipping problems written in bold text. The real count of open problems is 26 (two got fixed today, which is why the number moved). Also patched a small bug that could cause an error when starting a brand-new work session on a fresh checkout of the code. Nothing here touches bankroll, bets, or risk limits.
