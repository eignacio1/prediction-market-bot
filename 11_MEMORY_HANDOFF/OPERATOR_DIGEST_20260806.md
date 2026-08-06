# Operator Digest — 2026-08-06

**What changed today, in one paragraph:**
Continuing from yesterday's "22 stuck baseball bets" finding, we built a workaround and used it to actually resolve some of them. Five of the 22 got a real answer (won or lost) and a small profit — $15.84 — got booked. The other 17 turned out to be permanently stuck: we tried three different official sources for what actually happened in those games, and none of them have any record at all. That's not a bug we can fix by trying harder or waiting longer — the data simply doesn't exist for those specific dates. We wrote up a proposal for what to formally do with those 17 (declare them "closed, no result" instead of leaving them open forever), but the two decisions that matter most in that proposal are yours to make, not ours.

**What this means for your money:**
Small positive change: bankroll went from $683.91 to $733.75, mostly from the $15.84 profit plus getting $50+ of previously-frozen money back into play. $160.24 remains tied up in the 17 permanently-stuck bets and can't move until you decide what to do with it — still zero real money at risk either way, this is all paper trading.

**Does anything need your decision right now?**
Yes, one thing, not urgent: for those 17 permanently-stuck bets, should we count the $160.24 as simply removed from the books (like it was never bet), or count it as a loss? This changes our win-rate numbers either way, so we didn't want to guess. A short writeup (ADR-0051) lays out both options — should take a few minutes to read and decide.

**Anything that worried the session, even if not urgent:**
No new concerns. The underlying reasons these bets got stuck in the first place (a data-lookup bug plus baseball's official stats site periodically blocking our server) are still not fixed — today's fix was a manual, one-time workaround, not a permanent repair. That real fix is still on the to-do list, targeted for the next work window.

---

*Full technical detail: see `SESSION_HANDOFF_20260806_0044.md` and `DECISION_LOG.md` for 2026-08-05/06.*
