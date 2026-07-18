# Operator Digest — 2026-07-18

**What changed today, in one paragraph:**
We shipped the baseball batting-average fix you signed off on: instead of trusting a player's last-10-game average blindly (which is noisy for players who've only had a handful of at-bats recently), the model now leans more on the league-average baseline the fewer real at-bats a player has, and leans more on their own stats the more at-bats they've had. This is now live and feeding the bot's in-game baseball decisions.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears. This only changes how the model thinks, not any live trade.

**Does anything need your decision right now?**
No — nothing needs you today. The fix you approved yesterday is shipped and running; we're now waiting for enough new bets to accumulate under the fixed logic to confirm it actually worked as intended (that check isn't done yet, on purpose — needs more games to play out first).

**Anything that worried the session, even if not urgent:**
While wrapping up, we noticed another Claude session was working in the same shared files at the same time. Nothing was lost or overwritten — we checked carefully — but it's a reminder that when two sessions run in parallel without their own isolated workspace, there's a real risk of one accidentally erasing the other's work. Worth keeping an eye on if this happens again.

---

*Full technical detail: see `SESSION_HANDOFF_20260718_0044.md` and `DECISION_LOG.md` for this date.*
