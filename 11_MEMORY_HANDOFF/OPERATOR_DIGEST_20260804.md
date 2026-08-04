# Operator Digest — 2026-08-04

**What changed today, in one paragraph:**
A couple weeks ago we killed two planned bet types (player prop hits and run-line bets) because an early check of the market's order book depth said they were too thin to trade safely. Today we re-checked that same depth three separate times, spread across a live game slate instead of one snapshot, and the picture changed: player-prop depth actually looks fine now (passed two out of three checks), and one specific market swung by 14x in size within 14 minutes of us checking it twice. That volatility means we're not confident enough yet to update the official numbers in the project's main rulebook — we're flagging it for your review instead of guessing.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears. This was a research/verification task, not a trading session.

**Does anything need your decision right now?**
No — nothing urgent. But three things are sitting there waiting for your read when you have time: (1) whether to soften the "$500–$2,000" market-size language in the rulebook given today's volatile readings, (2) two other bet types (game winner and team total) came back with mixed pass/fail results across the three checks and need your call on whether to re-enable them, and (3) we found a bug in the tool that samples market depth (it can under-sample smaller markets) — not fixed, just flagged, since fixing it wasn't in scope today.

**Anything that worried the session, even if not urgent:**
The 14x swing in market depth within 14 minutes is worth knowing about even though nothing acted on it today — it's a reminder that a single snapshot-in-time check (like the one that killed these bet types originally) can be misleading in either direction.

---

*Full technical detail: see `SESSION_HANDOFF_20260804_0016.md` and `DECISION_LOG.md` for 2026-08-03.*
