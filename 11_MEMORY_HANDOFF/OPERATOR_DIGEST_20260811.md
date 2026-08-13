# Operator Digest — 2026-08-11

**What changed today, in one paragraph:**
Today's session added a rule that has been missing: from now on, an internal issue tracker entry can only be marked "fixed" if there's an actual automated check that would catch it happening again — or an explicit note saying why no such check is possible. This was prompted by comparing two past issues: one that stayed fixed because the fix was code, and one that came back within a day because the fix was only a written note. The written note turned out to be wrong, and nothing caught that until real trading data got corrupted by it.

**What this means for your money:**
No change today — still zero real money at risk. But this closes a real gap in how the safety net around the money-tracking ledger gets verified: the rule now also says the system can't go live until its data-integrity checks have run clean for a while, not just once. That's a stricter bar than existed before.

**Does anything need your decision right now?**
The new rule (a formal governance document) is written but not yet formally signed off — that sign-off is a "when convenient" item, not urgent. No trading logic or money-handling code was touched today.

**Anything that worried the session, even if not urgent:**
One thing: the automated check that would let the two issues above graduate from "flagged" to "fully resolved" is being built by a separate, parallel work session and isn't finished yet — so today's fix sets up the rule correctly but the actual safety check it depends on is still pending.

---

## T-436 — Phase 1 depth verdict, "Good to unblock"

**What changed today, in one paragraph:**
You asked for a fresh check of how deep the order books actually are on the six market types the bot trades — deep enough that a bet could actually get filled at a fair price, not just theoretically available. Four of six passed comfortably (game totals, game winner, run line, team total). Two (partial-game winner, player props) came in thin — well under the floor — but per your standing instruction, thin isn't the same as dead, so neither gets shut off. Along the way I found a contradiction in the internal planning notes: one document said the next phase of work stays blocked on an unrelated cleanup task regardless of what the depth check found. I flagged it rather than deciding it myself, and you said "Good to unblock" — so that phase of work (fixing some structural rough edges, not adding new markets) can now start.

**What this means for your money:**
No change today — still zero real money at risk. No bets were placed or resized. This was a measurement-and-paperwork session.

**Does anything need your decision right now?**
No — the one decision that needed you (whether the next phase should wait on that unrelated cleanup task) was already made in-session when you said "Good to unblock." Nothing else pending.

**Anything that worried the session, even if not urgent:**
The two thin-depth market types (partial-game winner, player props) are worth revisiting once there's fresh depth data — a FAIL today doesn't mean permanently unusable, but it also isn't something to forget about.

---

## T-437 (overnight into 2026-08-12) — outcome-authority verdict, one baseball strategy's track record gets corrected

**What changed today, in one paragraph:**
Two nights ago (T-429), a session found and fixed a bug where the live baseball in-play strategy (T4M-PROJ) was sometimes recording the wrong game's result against a bet — a wall-clock date bug — but a second, unexplained batch of disagreements between two different record-keeping systems was left open. Tonight's session tracked that second batch down: it re-checked a full sample of 69 disputed bets by pulling fresh data from the official source days after the games finished, and every single one agreed with the independent "shadow" record-keeper we built earlier, not with the bot's own ledger. That confirms a second, separate bug: the official stats source sometimes mislabels which game a stat belongs to for a day or two right after the game, then corrects itself. With that settled, the session went through all 1,220 flagged bets and fixed the 757 where the wrong-date bug had actually changed the recorded result — correcting wins to losses and vice versa where the evidence showed the original was wrong. 370 more were flagged but turned out to already have the right result by coincidence, and 93 still need more evidence before they can be corrected (that's now a separate to-do item).

**What this means for your money:**
No change to real money — still zero real money at risk. But this correction meaningfully changes what we can currently claim about this strategy's track record: after fixing the 757 bad records, the strategy's proven-clean track record shrank and got choppier (net -$110 across the corrected bets), which means the "is this strategy good enough to trust with real money" math now says **not yet** — it had briefly looked like it had crossed that bar, but the corrected numbers show it needs roughly 386 more clean, resolved bets before that claim would be accurate. This is the system doing exactly what it should: a bad number that briefly looked good just got fixed, and the bar didn't move, the data under it moved.

**Does anything need your decision right now?**
No — nothing needs you today. A follow-up item (finishing the correction for those last 93 bets) is scoped and ready for a future session to just pick up.

**Anything that worried the session, even if not urgent:**
The underlying question of exactly how long to wait before trusting a freshly-resolved bet's result (since the official source can be wrong for a day or two) is still an open design question, not yet decided — the evidence says "wrong at ~2 days, right by 7-11 days," but nobody has picked a specific rule yet (e.g., "always wait a week"). That's a small decision worth having on the list, not urgent.
## T-432 — Ledger invariant suite (data "smoke alarm")

**What changed today, in one paragraph:**
This is the direct fix for the incident where a bad date field silently corrupted about 44% of a batch of resolved bets, and nobody caught it for four separate work sessions because nothing actually checked whether the numbers in the ledger were *correct* — only that the process that writes them had run. Today's session built that missing check: a script that reads the ledger and independently verifies about a dozen things that should always be true (prices between 0 and 1, profit/loss sign matching win/loss, no position open in both directions on the same bet, etc.), and cross-checks resolved bets against a second, independently-built record of what actually happened in each game. Two of the checks you originally specified turned out to be slightly wrong as written — they would have falsely flagged good data as bad — so those two were corrected before being built, with the reasoning written down.

**What this means for your money:**
No change today — still zero real money at risk. This is a smoke alarm, not a fix: it's explicitly built to only warn, never to stop or block anything, per your instruction. It ran once and confirmed the earlier corruption issue is still only partially resolved (a related, already-known data problem is still live and being worked separately) — that's not a new problem, just confirmation the old one isn't fully closed yet.

**Does anything need your decision right now?**
No — nothing needs you today. The smoke alarm runs quietly in the background from now on. There's a written proposal for a future stricter mode, where it could actually block something instead of just warning — but that's not built, and it's explicitly your call whenever you want to consider it, not urgent.

**Anything that worried the session, even if not urgent:**
One small, isolated oddity turned up: one bet's ticker ID appears to be missing a letter, so it doesn't cleanly match the player's name. It's a single occurrence, doesn't look like it caused any actual harm, and has been noted for whoever next works on how those IDs get generated.

---
