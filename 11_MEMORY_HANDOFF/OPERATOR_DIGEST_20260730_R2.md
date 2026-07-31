# Operator Digest — 2026-07-30 (R2, signed edge gate fix)

**What changed today, in one paragraph:**
We found and fixed a bug in the bot's approval gate: it was supposed to reject bets where the "safety margin" (the gap between what the model expects and what it costs to trade) was too thin, but a math mistake made it treat a *negative* safety margin the same as a small positive one — so it was letting through bets it should have rejected. In one recent batch of past bet evaluations, this let through 239 bets, and every single one of them was actually a bad call. Fixed the math, and added a second independent check that catches a related mistake.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears. This fix doesn't turn any bet sizing back on; the "how much to bet" dial for all four strategies is still set to zero, exactly as you approved last session. This was purely a correctness fix so that dial is trustworthy whenever you do decide to turn it back on.

**Does anything need your decision right now?**
No — nothing needs you today. The fix is merged and tested (2,757 tests passing, same count as before).

**Anything that worried the session, even if not urgent:**
While making this fix, the automated tests caught that the fix itself would have silently broken an unrelated test if left unpatched — we caught and fixed that before merging, so nothing shipped broken. Also worth knowing: some of our recent findings about how well the model is performing were measured using data from before this bug was fixed, so those findings need to be re-checked against clean data going forward — not urgent, just flagged so nobody treats the old numbers as final.

---

*Full technical detail: see `SESSION_HANDOFF_20260730_0600.md` and `DECISION_LOG.md` for this date.*
