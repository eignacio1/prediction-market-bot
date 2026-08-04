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

## Update — later same day (T-413/VC6 close-out)

**What changed:**
A recent report (from July 30) had claimed the baseball live-market strategy was making about 11% return on the bets it approved. We went back and checked that number against exactly how the bot actually charges its trading fees, and found the report's math didn't quite match the real code — it was charging fees the wrong way for some bets. The real, verified number is a bit lower: about 9.6-9.7% return, not 11%. Still clearly positive, still a good result — the "this strategy works" conclusion holds — but the exact number was overstated by about 1.3 percentage points, and roughly 44 bets that shouldn't have counted were included.

**What this means for your money:**
No change — still zero real money at risk. This didn't touch any live code, any bet sizing, or anything the bot actually does. It's a correction to a written report's headline number, not a change to how the bot trades.

**Does anything need your decision right now?**
No — nothing needs you today. One follow-up is logged and waiting (not urgent): the original July 30 report itself should eventually get its headline number corrected to match what we verified today, but nobody's assigned to do that yet.

**Anything that worried the session, even if not urgent:**
No new concerns. This was exactly the kind of double-check this project's process is designed to catch — a number looked right, got questioned anyway, and turned out to need a small correction before anyone made a decision based on the wrong one.

---

## Update — later same day (T-414: baseball book "frozen" follow-up)

**What changed:**
You asked us to check on the baseball book — it looked frozen for four days — and figure out why. Mostly good news: it's frozen because the bot's main overnight strategy has its bet-sizing turned down to zero right now, on purpose, from a decision you already made about avoiding ruinous losing streaks (this is the same policy the update above discusses). It's still watching every game and doing the math, it's just not putting any money down while that's off. But we also found something new: 22 old paper bets from earlier this month are stuck open and can't be marked won or lost, because the source we use to look up final scores isn't returning results for those specific games even though they finished days ago. That's a separate problem from the sizing-being-off issue, and it's why the book's "last updated" timestamp hasn't moved.

**What this means for your money:**
No change to what's at risk today — still zero real money, paper trading only. But those 22 stuck paper bets are holding paper capital that can't be freed up or counted toward the finish line (the "resolved bets" count needed before real money is ever allowed) under how the system currently works. Not losing money, just stuck.

**Does anything need your decision right now?**
Yes, one thing, not urgent: should we treat the 22 stuck bets as a real problem worth logging and building a fix for (e.g., giving old unresolvable bets a way to close out instead of hanging forever), or is this fine to leave as-is? We didn't make that call ourselves since it's a judgment about severity — flagging it for you instead of guessing.

**Anything that worried the session, even if not urgent:**
Just the stuck-bets item above. Separately, we checked in on the market-depth data collection mentioned in the updates above — it's healthy and on track, evenly collecting data across all bet types now — and set a specific date (August 9th) to check back once enough data has accumulated, so it doesn't quietly sit half-finished.

---

*Full technical detail: see `SESSION_HANDOFF_20260804_0525.md`, `SESSION_HANDOFF_20260804_2335.md`, `SESSION_HANDOFF_20260804_0456.md`, `SESSION_HANDOFF_20260804_0050.md`, `SESSION_HANDOFF_20260804_0016.md`, `DECISION_LOG.md`, and `10_INFRA_OPERATIONS/OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md` for 2026-08-03/2026-08-04.*

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

*Full technical detail: see `SESSION_HANDOFF_20260804_0520.md`, `SESSION_HANDOFF_20260804_2335.md`, `SESSION_HANDOFF_20260804_0456.md`, `SESSION_HANDOFF_20260804_0050.md`, `SESSION_HANDOFF_20260804_0016.md`, and `DECISION_LOG.md` for 2026-08-03/2026-08-04.*
