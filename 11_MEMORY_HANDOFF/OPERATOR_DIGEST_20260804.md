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

## Update — later same day (Phase 0-H / T-412)

**What changed:**
Closed out all three open items from earlier today. (1) Found and fixed the actual bug in the depth-sampling tool — it was reading markets unevenly (grabbing the first few it saw instead of a fair spread) and it was also accidentally checking a season-long leaderboard market instead of the daily hits market for one entire pass, which is why the original depth reading was misleadingly low. Fixed both, added tests so it can't silently regress. (2) Turned depth-checking from a one-off manual task into an automatic cron job that now runs continuously on the server and is already accumulating real data (confirmed it deployed and fired correctly, checked the bot's health before and after). (3) Updated the rulebook (CLAUDE.md) to stop stating a specific dollar range for market depth — instead it now says plainly that depth swings 10-100x within a day and any sizing decision needs to check live data, not a written number.

**Still open, still needs your read when you have time:**
Game winner and team total bet types remain a mixed picture (one passed before the game started, then failed once the game was underway) — deliberately not declaring them dead or safe; more data points are now accumulating automatically via the new cron job. Also newly flagged: the paper-trading engine currently never checks whether a bet would actually have filled at the size claimed against the real order book — it assumes every fill happens at the midpoint price. This is now logged as a precondition that must be resolved before any real money is authorized (it doesn't block today, but it's now on record as a blocker for that future gate).

**Does anything need your decision right now?**
No — nothing urgent. Still zero real money at risk.

---

## Update — later same day (PRICE_ARCHIVE sync/backup cleanup)

**What changed:**
Earlier sessions today said the tool that continuously records market prices "was working" on the server. But nobody had actually checked whether a copy of that data existed anywhere except that one server's disk — and this season's price data can't be regenerated once it's gone. This session double-checked directly: yes, it's genuinely running and collecting data. But there was no backup, and the folder wasn't even protected from being accidentally deleted from our records by a routine save. Fixed both — added the protection, and set up an automatic copy that pulls the data down to a second location every time anyone works on this project going forward.

**What this means for your money:**
No change — still zero real money at risk. This was a data-safety fix, not a trading change.

**Does anything need your decision right now?**
No — nothing urgent. One thing on record for later, not now: a proper cloud backup (beyond the second-copy fix made today) would be worth doing before the season gets much further along, but that's a bigger task than today's fix and doesn't need a decision this moment.

**Anything that worried the session, even if not urgent:**
Three separate check-ins over the past couple weeks all said this data collection was "verified" or "deployed" without anyone actually confirming a backup existed. That's now flagged as a pattern to watch for — a check that says "it's working" isn't the same as a check that tests the thing that actually matters (in this case, "is the only copy safe").

---

*Full technical detail: see `SESSION_HANDOFF_20260804_0456.md`, `SESSION_HANDOFF_20260804_0050.md`, `SESSION_HANDOFF_20260804_0016.md`, and `DECISION_LOG.md` for 2026-08-03/2026-08-04.*

---

## Update — later same day (T-415 citation repair)

**What changed:**
Housekeeping only. Some of the project's internal planning documents had drifted — they pointed to specific file locations and counts that were true when written but had since moved or changed, the kind of thing that quietly misleads whoever reads them next. Found and fixed four of these stale references, double-checking each one against the real, current file rather than trusting the old note. Also logged this as a general failure pattern worth watching for again, and proposed (but didn't yet build) an automated check that would catch this kind of drift on its own going forward.

**What this means for your money:**
No change — still zero real money at risk. Nothing today touched trading logic, risk limits, or the go-live gate.

**Does anything need your decision right now?**
No — nothing needs you today.

**Anything that worried the session, even if not urgent:**
No new concerns. One thing corrected along the way: one of the documents claimed a piece of NBA-related code had "no test coverage" — checked it directly and that wasn't quite right (it does have basic tests; what it actually lacks is real-world exercise, since NBA trading is still paused). Fixed the document to say the accurate thing instead of repeating the imprecise claim.

*Full technical detail for this update: see `SESSION_HANDOFF_20260804_0520.md` and `DECISION_LOG.md` 2026-08-04 (T-415 entry).*
